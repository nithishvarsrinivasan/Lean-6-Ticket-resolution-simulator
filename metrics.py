# =============================================================================
# metrics.py — Metrics Logger for Both Simulation Engines
# =============================================================================
# Tracks resolution time, waiting time, reassignments, throughput, and queue
# size independently for Traditional and Lean engines.
# Thread-safe via threading.Lock.
# =============================================================================

import threading
import time
from collections import deque
from typing import Deque, Dict, List, Optional

import config


class MetricsStore:
    """
    Holds all tracked metrics for ONE engine (Traditional OR Lean).

    All public methods are thread-safe.
    """

    def __init__(self, name: str):
        self.name: str = name
        self._lock = threading.Lock()

        # Counters
        self._total_resolved:     int   = 0
        self._total_reassignments: int  = 0

        # Accumulation lists (for averages)
        self._resolution_times: List[float] = []   # seconds per resolved ticket
        self._waiting_times:    List[float] = []   # seconds in queue per ticket

        # Throughput tracking: timestamps of resolutions in last 60 s
        self._resolution_timestamps: Deque[float] = deque()

        # Queue size history: list of (timestamp, size) tuples
        self._queue_size_history: List[tuple] = []

    # ------------------------------------------------------------------
    # Recording events
    # ------------------------------------------------------------------

    def record_resolution(
        self,
        resolution_time: float,
        waiting_time: float,
        reassignments: int,
    ) -> None:
        """Call once when a ticket is resolved."""
        now = time.time()
        with self._lock:
            self._total_resolved += 1
            self._total_reassignments += reassignments
            self._resolution_times.append(resolution_time)
            self._waiting_times.append(waiting_time)
            self._resolution_timestamps.append(now)
            # Remove timestamps older than 60 seconds (sliding window)
            cutoff = now - 60.0
            while self._resolution_timestamps and self._resolution_timestamps[0] < cutoff:
                self._resolution_timestamps.popleft()

    def record_queue_size(self, size: int) -> None:
        """Call periodically to capture queue depth snapshots."""
        with self._lock:
            self._queue_size_history.append((time.time(), size))
            # Keep last 200 snapshots
            if len(self._queue_size_history) > 200:
                self._queue_size_history.pop(0)

    # ------------------------------------------------------------------
    # Derived metrics (read-only)
    # ------------------------------------------------------------------

    @property
    def total_resolved(self) -> int:
        with self._lock:
            return self._total_resolved

    @property
    def total_reassignments(self) -> int:
        with self._lock:
            return self._total_reassignments

    @property
    def avg_resolution_time(self) -> float:
        """Average resolution time in seconds (0.0 if no data)."""
        with self._lock:
            if not self._resolution_times:
                return 0.0
            return sum(self._resolution_times) / len(self._resolution_times)

    @property
    def avg_waiting_time(self) -> float:
        """Average queue waiting time in seconds (0.0 if no data)."""
        with self._lock:
            if not self._waiting_times:
                return 0.0
            return sum(self._waiting_times) / len(self._waiting_times)

    @property
    def throughput_per_minute(self) -> float:
        """Tickets resolved in the last 60 seconds."""
        with self._lock:
            return float(len(self._resolution_timestamps))

    @property
    def queue_size_history(self) -> List[tuple]:
        """Copy of queue size history [(timestamp, size), ...]."""
        with self._lock:
            return list(self._queue_size_history)

    @property
    def resolution_times_series(self) -> List[float]:
        """Copy of per-ticket resolution times list."""
        with self._lock:
            return list(self._resolution_times)

    def snapshot(self) -> Dict:
        """Return a dictionary snapshot of all metrics for display."""
        return {
            "name":                self.name,
            "total_resolved":      self.total_resolved,
            "total_reassignments": self.total_reassignments,
            "avg_resolution_time": round(self.avg_resolution_time, 2),
            "avg_waiting_time":    round(self.avg_waiting_time, 2),
            "throughput_per_min":  round(self.throughput_per_minute, 1),
        }

    def reset(self) -> None:
        """Clear all recorded data."""
        with self._lock:
            self._total_resolved       = 0
            self._total_reassignments  = 0
            self._resolution_times.clear()
            self._waiting_times.clear()
            self._resolution_timestamps.clear()
            self._queue_size_history.clear()


class MetricsLogger:
    """
    Holds MetricsStore instances for BOTH engines and provides combined views.
    """

    def __init__(self):
        self.traditional = MetricsStore("Traditional")
        self.lean        = MetricsStore("Lean Six Sigma")

    @property
    def combined_resolved(self) -> int:
        """Total tickets resolved across both systems."""
        return self.traditional.total_resolved + self.lean.total_resolved

    def should_show_summary(self) -> bool:
        """True once both engines together have resolved the summary trigger count."""
        return self.combined_resolved >= config.SUMMARY_TRIGGER_COUNT

    def improvement_pct(self) -> Optional[float]:
        """
        Percentage improvement of Lean over Traditional in avg resolution time.
        Returns None if either has no data.
        """
        t = self.traditional.avg_resolution_time
        l = self.lean.avg_resolution_time
        if t == 0.0 or l == 0.0:
            return None
        return round((t - l) / t * 100, 1)

    def reset(self) -> None:
        """Reset both metric stores."""
        self.traditional.reset()
        self.lean.reset()
