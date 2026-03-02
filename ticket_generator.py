# =============================================================================
# ticket_generator.py — Shared Ticket Generator
# =============================================================================
# Generates Ticket objects continuously and feeds IDENTICAL tickets to both
# the Traditional and Lean engines. Uses threading.Event for pause/resume.
# =============================================================================

import random
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import config


@dataclass
class Ticket:
    """Represents a single helpdesk support ticket."""
    id:              int
    issue_type:      str          # e.g. "Network"
    priority:        str          # "High" | "Medium" | "Low"
    department:      str          # originating department
    timestamp:       datetime     # creation time
    assigned_team:   str  = ""    # populated by engine
    status:          str  = "Pending"  # Pending | Processing | Resolved | Reassigned
    resolution_time: float = 0.0  # seconds taken to resolve
    waiting_time:    float = 0.0  # seconds spent in queue before processing
    reassignments:   int  = 0     # how many times ticket was re-routed

    def clone(self) -> "Ticket":
        """Return a shallow copy so each engine gets an independent instance."""
        from copy import copy
        return copy(self)


class TicketGenerator:
    """
    Continuously generates Ticket objects and pushes them to registered queues.

    Both the Traditional and Lean engines register their queues; every ticket
    generated is cloned and appended to all registered queues so both systems
    process exactly the same workload.
    """

    def __init__(self):
        self._ticket_counter: int = 0          # monotonic ID counter
        self._queues: List[List[Ticket]] = []  # registered engine queues
        self._lock = threading.Lock()           # protects counter & queues list
        self._stop_event  = threading.Event()  # signals thread to stop
        self._pause_event = threading.Event()  # cleared = paused; set = running
        self._pause_event.set()                # start in running state
        self._thread: Optional[threading.Thread] = None
        # Mutable arrival interval (seconds); guarded by _lock
        self._arrival_min: float = config.TICKET_ARRIVAL_MIN_SEC
        self._arrival_max: float = config.TICKET_ARRIVAL_MAX_SEC

    # ------------------------------------------------------------------
    # Queue registration
    # ------------------------------------------------------------------

    def register_queue(self, queue: list) -> None:
        """Register a list that will receive cloned Ticket objects."""
        with self._lock:
            self._queues.append(queue)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Spawn the background generator thread."""
        self._stop_event.clear()
        self._pause_event.set()
        self._thread = threading.Thread(
            target=self._generate_loop, daemon=True, name="TicketGenerator"
        )
        self._thread.start()

    def pause(self) -> None:
        """Pause ticket generation (thread stays alive)."""
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume ticket generation."""
        self._pause_event.set()

    def stop(self) -> None:
        """Stop and join the generator thread."""
        self._stop_event.set()
        self._pause_event.set()  # unblock if paused
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def reset(self) -> None:
        """Stop generation and flush all registered queues."""
        self.stop()
        with self._lock:
            self._ticket_counter = 0
            for q in self._queues:
                q.clear()
            self._arrival_min = config.TICKET_ARRIVAL_MIN_SEC
            self._arrival_max = config.TICKET_ARRIVAL_MAX_SEC

    # ------------------------------------------------------------------
    # Load control
    # ------------------------------------------------------------------

    def increase_load(self) -> None:
        """Decrease inter-arrival time → more tickets per minute."""
        with self._lock:
            self._arrival_min = max(
                config.LOAD_MIN, self._arrival_min - config.LOAD_STEP
            )
            self._arrival_max = max(
                config.LOAD_MIN + 0.5, self._arrival_max - config.LOAD_STEP
            )

    def decrease_load(self) -> None:
        """Increase inter-arrival time → fewer tickets per minute."""
        with self._lock:
            self._arrival_min = min(
                config.LOAD_MAX - 0.5, self._arrival_min + config.LOAD_STEP
            )
            self._arrival_max = min(
                config.LOAD_MAX, self._arrival_max + config.LOAD_STEP
            )

    # ------------------------------------------------------------------
    # Internal generation loop
    # ------------------------------------------------------------------

    def _generate_loop(self) -> None:
        """Background loop: creates tickets and distributes to all queues."""
        while not self._stop_event.is_set():
            # Block here if paused
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            ticket = self._make_ticket()

            with self._lock:
                for q in self._queues:
                    q.append(ticket.clone())   # each engine gets its own copy

            # Wait for next arrival (sampled inside lock to read current values)
            with self._lock:
                lo, hi = self._arrival_min, self._arrival_max
            sleep_dur = random.uniform(lo, hi)
            self._stop_event.wait(timeout=sleep_dur)  # interruptible sleep

    def _make_ticket(self) -> Ticket:
        """Create a new Ticket with randomised fields."""
        with self._lock:
            self._ticket_counter += 1
            tid = self._ticket_counter

        priorities = list(config.PRIORITY_WEIGHTS.keys())
        weights    = list(config.PRIORITY_WEIGHTS.values())

        return Ticket(
            id          = tid,
            issue_type  = random.choice(config.ISSUE_TYPES),
            priority    = random.choices(priorities, weights=weights, k=1)[0],
            department  = random.choice(config.DEPARTMENTS),
            timestamp   = datetime.now(),
        )

    # ------------------------------------------------------------------
    # Properties (read-only access for the UI)
    # ------------------------------------------------------------------

    @property
    def total_generated(self) -> int:
        """Total tickets created since last reset."""
        with self._lock:
            return self._ticket_counter

    @property
    def current_interval(self) -> str:
        """Human-readable arrival interval for UI display."""
        with self._lock:
            return f"{self._arrival_min:.1f}s – {self._arrival_max:.1f}s"
