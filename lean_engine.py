# =============================================================================
# lean_engine.py — Lean Six Sigma Helpdesk Engine (Optimised Model)
# =============================================================================
# Simulates an optimised, rule-based helpdesk system with:
#   • Automated rule-based categorisation (1 s fixed)
#   • Direct routing to the correct team (no reassignments)
#   • Optimised resolution delay (5–10 s)
#   • Detailed processing log
# =============================================================================

import threading
import time
import random
from datetime import datetime
from typing import List

import config
from metrics import MetricsStore
from ticket_generator import Ticket


class LeanEngine:
    """
    Processes tickets using Lean Six Sigma optimised rules.

    One worker thread continuously picks tickets from the incoming queue,
    applies deterministic routing and minimal delays, then marks tickets resolved.
    No reassignments ever occur in this engine.
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
            target=self._process_loop, daemon=True, name="LeanEngine"
        )
        self._thread.start()
        self._log("🟡 Lean Six Sigma engine started.")

    def pause(self) -> None:
        """Pause processing."""
        self._pause_event.clear()
        self._log("⏸ Lean engine paused.")

    def resume(self) -> None:
        """Resume processing."""
        self._pause_event.set()
        self._log("▶ Lean engine resumed.")

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
                time.sleep(0.2)
                continue

            self._process_ticket(ticket)

    def _dequeue(self) -> Ticket | None:
        """Pop the next ticket from the queue (FIFO)."""
        with self._lock:
            if self.queue:
                return self.queue.pop(0)
        return None

    def _process_ticket(self, ticket: Ticket) -> None:
        """
        Run the Lean Six Sigma processing pipeline for one ticket:
            1. Record wait time
            2. Deterministic routing via LEAN_ROUTING config
            3. Automated classification delay (fixed 1 s)
            4. Resolution delay (5–10 s)
            5. Record metrics (0 reassignments — guaranteed)
        """
        arrival_time = time.time()

        # --- 1. Mark as Processing + route to correct team ---
        ticket.status = "Processing"
        correct_team  = config.LEAN_ROUTING.get(ticket.issue_type, "General Support")
        ticket.assigned_team = correct_team
        self._log(
            f"🔵 #{ticket.id} [{ticket.issue_type}] → {correct_team} (auto-routed)"
        )

        # --- 2. Automated classification delay (fixed, minimal) ---
        self._interruptible_sleep(config.LEAN_CLASSIFICATION_DELAY)
        if self._stop_event.is_set():
            return

        # --- 3. Resolution delay (shorter range than traditional) ---
        res_delay = random.uniform(
            config.LEAN_RESOLUTION_MIN, config.LEAN_RESOLUTION_MAX
        )
        self._interruptible_sleep(res_delay)
        if self._stop_event.is_set():
            return

        # --- 4. Mark resolved (NO reassignment can occur) ---
        end_time        = time.time()
        waiting_time    = arrival_time - ticket.timestamp.timestamp()
        resolution_time = end_time - arrival_time
        ticket.status          = "Resolved"
        ticket.resolution_time = resolution_time
        ticket.waiting_time    = waiting_time
        ticket.reassignments   = 0   # Lean system never reassigns

        with self._lock:
            self.resolved.append(ticket)

        self._metrics.record_resolution(resolution_time, waiting_time, reassignments=0)
        self._metrics.record_queue_size(self.queue_size)
        self._log(
            f"🟢 #{ticket.id} Resolved by {correct_team} "
            f"in {resolution_time:.1f}s (no reassignments)"
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
                for t in self.queue[:10]
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
