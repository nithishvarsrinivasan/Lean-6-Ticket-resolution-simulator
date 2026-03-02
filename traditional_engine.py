# =============================================================================
# traditional_engine.py — Traditional Helpdesk Engine (Inefficient Model)
# =============================================================================
# Simulates a manual, unoptimised helpdesk system with:
#   • Random team assignment
#   • Manual classification delay (5–12 s)
#   • 40 % chance of wrong assignment → reassignment delay (6 s)
#   • Resolution delay (5–15 s)
#   • Detailed processing log
# =============================================================================

import random
import threading
import time
from datetime import datetime
from typing import List

import config
from metrics import MetricsStore
from ticket_generator import Ticket


class TraditionalEngine:
    """
    Processes tickets using traditional, inefficient helpdesk rules.

    One worker thread continuously picks tickets from the incoming queue,
    simulates delays and mis-assignments, then marks tickets resolved.
    All state mutations are protected by a threading.Lock.
    """

    def __init__(self, metrics: MetricsStore):
        self._metrics = metrics
        self._lock    = threading.Lock()

        # Incoming queue: Ticket objects appended by TicketGenerator
        self.queue: List[Ticket] = []

        # Resolved tickets list (for display)
        self.resolved: List[Ticket] = []

        # Human-readable event log shown in the UI panel
        self.log: List[str] = []

        # Threading controls
        self._stop_event  = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()   # start unpaused
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background worker thread."""
        self._stop_event.clear()
        self._pause_event.set()
        self._thread = threading.Thread(
            target=self._process_loop, daemon=True, name="TraditionalEngine"
        )
        self._thread.start()
        self._log("🟡 Traditional engine started.")

    def pause(self) -> None:
        """Pause processing."""
        self._pause_event.clear()
        self._log("⏸ Traditional engine paused.")

    def resume(self) -> None:
        """Resume processing."""
        self._pause_event.set()
        self._log("▶ Traditional engine resumed.")

    def stop(self) -> None:
        """Stop the worker thread."""
        self._stop_event.set()
        self._pause_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def reset(self) -> None:
        """Stop engine and clear all state."""
        self.stop()
        with self._lock:
            self.queue.clear()
            self.resolved.clear()
            self.log.clear()
        self._metrics.reset()

    # ------------------------------------------------------------------
    # Internal processing loop
    # ------------------------------------------------------------------

    def _process_loop(self) -> None:
        """Continuously pick and process tickets from the queue."""
        while not self._stop_event.is_set():
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            ticket = self._dequeue()
            if ticket is None:
                # No ticket available; busy-wait briefly
                time.sleep(0.2)
                continue

            self._process_ticket(ticket)

    def _dequeue(self) -> Ticket | None:
        """Pop the highest-priority ticket from the front of the queue (FIFO)."""
        with self._lock:
            if self.queue:
                return self.queue.pop(0)
        return None

    def _process_ticket(self, ticket: Ticket) -> None:
        """
        Run the full traditional processing pipeline for one ticket:
            1. Record wait time
            2. Random team assignment
            3. Manual classification delay
            4. Possible wrong assignment + reassignment delay
            5. Resolution delay
            6. Record metrics
        """
        arrival_time = time.time()

        # --- 1. Mark as Processing ---
        ticket.status = "Processing"
        ticket.assigned_team = random.choice(config.TRADITIONAL_TEAMS)
        self._log(
            f"🔵 #{ticket.id} [{ticket.issue_type}] assigned to {ticket.assigned_team}"
        )

        # --- 2. Manual classification delay ---
        cls_delay = random.uniform(
            config.TRAD_CLASSIFICATION_MIN, config.TRAD_CLASSIFICATION_MAX
        )
        self._interruptible_sleep(cls_delay)
        if self._stop_event.is_set():
            return

        # --- 3. Wrong assignment check (40 % chance) ---
        reassignment_count = 0
        if random.random() < config.TRAD_WRONG_ASSIGN_PROB:
            ticket.status = "Reassigned"
            old_team = ticket.assigned_team
            # Pick a different team for reassignment
            new_team = random.choice(
                [t for t in config.TRADITIONAL_TEAMS if t != old_team]
            )
            ticket.assigned_team  = new_team
            ticket.reassignments += 1
            reassignment_count    += 1
            self._log(
                f"🔴 #{ticket.id} WRONG ASSIGNMENT! Reassigned from "
                f"{old_team} → {new_team}"
            )
            self._interruptible_sleep(config.TRAD_REASSIGN_DELAY)
            if self._stop_event.is_set():
                return
            ticket.status = "Processing"

        # --- 4. Resolution delay ---
        res_delay = random.uniform(
            config.TRAD_RESOLUTION_MIN, config.TRAD_RESOLUTION_MAX
        )
        self._interruptible_sleep(res_delay)
        if self._stop_event.is_set():
            return

        # --- 5. Mark resolved ---
        end_time        = time.time()
        waiting_time    = arrival_time - ticket.timestamp.timestamp()
        resolution_time = end_time - arrival_time
        ticket.status          = "Resolved"
        ticket.resolution_time = resolution_time
        ticket.waiting_time    = waiting_time
        ticket.reassignments   = reassignment_count

        with self._lock:
            self.resolved.append(ticket)

        self._metrics.record_resolution(resolution_time, waiting_time, reassignment_count)
        self._metrics.record_queue_size(self.queue_size)
        self._log(
            f"🟢 #{ticket.id} Resolved by {ticket.assigned_team} "
            f"in {resolution_time:.1f}s "
            f"(reassignments: {reassignment_count})"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _interruptible_sleep(self, seconds: float) -> None:
        """Sleep that wakes immediately if stop is signalled or engine is paused."""
        deadline = time.time() + seconds
        while time.time() < deadline:
            if self._stop_event.is_set():
                return
            if not self._pause_event.is_set():
                self._pause_event.wait()
            time.sleep(0.1)

    def _log(self, message: str) -> None:
        """Append a timestamped message to the event log (thread-safe)."""
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {message}"
        with self._lock:
            self.log.append(entry)
            # Keep log bounded
            if len(self.log) > config.MAX_LOG_DISPLAY * 3:
                self.log = self.log[-config.MAX_LOG_DISPLAY * 3:]

    # ------------------------------------------------------------------
    # Read-only properties for UI
    # ------------------------------------------------------------------

    @property
    def queue_size(self) -> int:
        with self._lock:
            return len(self.queue)

    @property
    def resolved_count(self) -> int:
        with self._lock:
            return len(self.resolved)

    def get_log(self) -> List[str]:
        """Return a copy of the most recent log entries."""
        with self._lock:
            return list(self.log[-config.MAX_LOG_DISPLAY:])

    def get_queue_snapshot(self) -> List[dict]:
        """Return a display-ready snapshot of the current queue."""
        with self._lock:
            return [
                {
                    "ID":       t.id,
                    "Type":     t.issue_type,
                    "Priority": t.priority,
                    "Dept":     t.department,
                    "Status":   config.STATUS_COLORS.get(t.status, t.status),
                }
                for t in self.queue[:10]   # show top 10
            ]

    def get_resolved_snapshot(self) -> List[dict]:
        """Return a display-ready snapshot of recently resolved tickets."""
        with self._lock:
            recent = self.resolved[-10:]
        return [
            {
                "ID":          t.id,
                "Type":        t.issue_type,
                "Team":        t.assigned_team,
                "ResTime (s)": round(t.resolution_time, 1),
                "Reassign":    t.reassignments,
            }
            for t in reversed(recent)
        ]
