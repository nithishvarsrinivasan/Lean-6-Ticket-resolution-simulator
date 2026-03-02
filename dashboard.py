# =============================================================================
# dashboard.py — Matplotlib Chart Rendering Functions
# =============================================================================
# All chart functions accept pre-collected metric data and return matplotlib
# Figure objects that Streamlit renders via st.pyplot().
# Each chart is independent; all use a dark-themed style.
# =============================================================================

import matplotlib
matplotlib.use("Agg")   # non-interactive backend required for Streamlit

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import List, Tuple

# --------------- Shared Style Constants ---------------
TRAD_COLOR  = "#E74C3C"   # Red  — Traditional
LEAN_COLOR  = "#2ECC71"   # Green — Lean Six Sigma
BG_COLOR    = "#1E1E2E"   # Dark background
PANEL_COLOR = "#2A2A3E"   # Slightly lighter panel
TEXT_COLOR  = "#ECECEC"   # Light text
GRID_COLOR  = "#3A3A5C"   # Subtle grid lines


def _apply_dark_style(ax: plt.Axes, fig: plt.Figure) -> None:
    """Apply consistent dark theme to any Axes and Figure."""
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(PANEL_COLOR)
    ax.tick_params(colors=TEXT_COLOR)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    ax.spines[:].set_color(GRID_COLOR)
    ax.grid(True, color=GRID_COLOR, linestyle="--", alpha=0.5)


# =============================================================================
# Chart 1 — Average Resolution Time Comparison (Bar Chart)
# =============================================================================

def chart_avg_resolution_time(
    trad_avg: float,
    lean_avg: float,
) -> plt.Figure:
    """
    Horizontal bar chart comparing average resolution times (seconds).

    Args:
        trad_avg: Traditional system average resolution time (s)
        lean_avg: Lean system average resolution time (s)
    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(6, 2.8))
    _apply_dark_style(ax, fig)

    labels = ["Traditional", "Lean Six Sigma"]
    values = [trad_avg, lean_avg]
    colors = [TRAD_COLOR, LEAN_COLOR]

    bars = ax.barh(labels, values, color=colors, height=0.5, edgecolor=GRID_COLOR)

    # Value annotations
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}s", va="center", color=TEXT_COLOR, fontsize=10, fontweight="bold"
        )

    ax.set_xlabel("Avg Resolution Time (seconds)", color=TEXT_COLOR)
    ax.set_title("⏱ Avg Resolution Time Comparison", color=TEXT_COLOR, fontsize=11, pad=8)
    ax.set_xlim(0, max(values) * 1.3 + 1)
    fig.tight_layout()
    return fig


# =============================================================================
# Chart 2 — Reassignments Comparison (Bar Chart)
# =============================================================================

def chart_reassignments(
    trad_reassign: int,
    lean_reassign: int,
) -> plt.Figure:
    """
    Bar chart comparing total ticket reassignments.

    Args:
        trad_reassign: Total reassignments in Traditional system
        lean_reassign: Total reassignments in Lean system
    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(6, 2.8))
    _apply_dark_style(ax, fig)

    labels = ["Traditional", "Lean Six Sigma"]
    values = [trad_reassign, lean_reassign]
    colors = [TRAD_COLOR, LEAN_COLOR]

    bars = ax.bar(labels, values, color=colors, width=0.4, edgecolor=GRID_COLOR)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
            str(val), ha="center", color=TEXT_COLOR, fontsize=11, fontweight="bold"
        )

    ax.set_ylabel("Total Reassignments", color=TEXT_COLOR)
    ax.set_title("🔄 Reassignments Comparison", color=TEXT_COLOR, fontsize=11, pad=8)
    ax.set_ylim(0, max(values) * 1.4 + 1)
    fig.tight_layout()
    return fig


# =============================================================================
# Chart 3 — Throughput Comparison (Bar Chart)
# =============================================================================

def chart_throughput(
    trad_tpm: float,
    lean_tpm: float,
) -> plt.Figure:
    """
    Bar chart comparing throughput (tickets resolved per last 60 seconds).

    Args:
        trad_tpm: Traditional system throughput per minute
        lean_tpm: Lean system throughput per minute
    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(6, 2.8))
    _apply_dark_style(ax, fig)

    labels  = ["Traditional", "Lean Six Sigma"]
    values  = [trad_tpm, lean_tpm]
    colors  = [TRAD_COLOR, LEAN_COLOR]

    bars = ax.bar(labels, values, color=colors, width=0.4, edgecolor=GRID_COLOR)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
            f"{val:.1f}", ha="center", color=TEXT_COLOR, fontsize=11, fontweight="bold"
        )

    ax.set_ylabel("Tickets / Last 60s", color=TEXT_COLOR)
    ax.set_title("🚀 Throughput Comparison", color=TEXT_COLOR, fontsize=11, pad=8)
    ax.set_ylim(0, max(values) * 1.4 + 0.5)
    fig.tight_layout()
    return fig


# =============================================================================
# Chart 4 — Queue Size Trend (Line Chart)
# =============================================================================

def chart_queue_size_trend(
    trad_history: List[Tuple[float, int]],
    lean_history: List[Tuple[float, int]],
) -> plt.Figure:
    """
    Line chart showing queue depth over time for both systems.

    Args:
        trad_history: List of (timestamp, queue_size) from Traditional engine
        lean_history: List of (timestamp, queue_size) from Lean engine
    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(6, 2.8))
    _apply_dark_style(ax, fig)

    def _norm_time(history):
        """Normalise timestamps to seconds-since-start."""
        if not history:
            return [], []
        t0 = history[0][0]
        xs = [h[0] - t0 for h in history]
        ys = [h[1] for h in history]
        return xs, ys

    tx, ty = _norm_time(trad_history)
    lx, ly = _norm_time(lean_history)

    if tx:
        ax.plot(tx, ty, color=TRAD_COLOR, linewidth=2, label="Traditional", alpha=0.9)
    if lx:
        ax.plot(lx, ly, color=LEAN_COLOR, linewidth=2, label="Lean Six Sigma", alpha=0.9)

    ax.set_xlabel("Elapsed Time (s)", color=TEXT_COLOR)
    ax.set_ylabel("Queue Depth", color=TEXT_COLOR)
    ax.set_title("📈 Queue Size Trend", color=TEXT_COLOR, fontsize=11, pad=8)

    legend = ax.legend(
        facecolor=PANEL_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=9
    )
    fig.tight_layout()
    return fig


# =============================================================================
# Summary Improvement Chart (bonus visual for final summary panel)
# =============================================================================

def chart_improvement_summary(
    trad_avg: float,
    lean_avg: float,
    improvement_pct: float,
) -> plt.Figure:
    """
    Stacked / comparison bar with improvement % annotation.
    Used in the final summary panel.
    """
    fig, ax = plt.subplots(figsize=(7, 3))
    _apply_dark_style(ax, fig)

    labels = ["Traditional", "Lean Six Sigma"]
    values = [trad_avg, lean_avg]
    colors = [TRAD_COLOR, LEAN_COLOR]

    bars = ax.bar(labels, values, color=colors, width=0.45, edgecolor=GRID_COLOR)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.4,
            f"{val:.1f}s",
            ha="center", color=TEXT_COLOR, fontsize=12, fontweight="bold"
        )

    if improvement_pct is not None:
        ax.annotate(
            f"🏆 {improvement_pct:.1f}% faster",
            xy=(1, lean_avg), xytext=(1.3, lean_avg + (trad_avg - lean_avg) / 2),
            fontsize=12, color="#F1C40F", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#F1C40F"),
        )

    ax.set_ylabel("Avg Resolution Time (s)", color=TEXT_COLOR)
    ax.set_title("🎯 Final Performance Summary", color=TEXT_COLOR, fontsize=12, pad=10)
    ax.set_ylim(0, max(values) * 1.5)
    fig.tight_layout()
    return fig
