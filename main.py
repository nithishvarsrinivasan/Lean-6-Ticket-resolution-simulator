# =============================================================================
# main.py — Streamlit Application Entry Point
# =============================================================================
#
# HOW TO RUN:
#   1. Install dependencies:
#         pip install streamlit matplotlib
#   2. From this directory, run:
#         streamlit run main.py
#   3. The app opens at http://localhost:8501
#
# ARCHITECTURE OVERVIEW:
#   • TicketGenerator  → creates tickets and feeds both engine queues
#   • TraditionalEngine → processes tickets with manual, inefficient logic
#   • LeanEngine        → processes tickets with rule-based, optimised logic
#   • MetricsLogger     → thread-safe metric accumulation for both engines
#   • dashboard.py      → matplotlib chart factories
#   • config.py         → all constants (no hardcoded values in this file)
#
# Streamlit session_state holds the singleton instances so they survive reruns.
# st_autorefresh (via an empty placeholder + time.sleep loop) drives live updates.
# =============================================================================

import time
import streamlit as st
import pandas as pd

# ── Local modules ──────────────────────────────────────────────────────────────
import config
from ticket_generator import TicketGenerator
from traditional_engine import TraditionalEngine
from lean_engine import LeanEngine
from metrics import MetricsLogger
import dashboard as dash

# =============================================================================
# Page configuration
# =============================================================================

st.set_page_config(
    page_title="LSS Helpdesk Simulation",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# Custom CSS — dark theme, status badge colours, panel styling
# =============================================================================

st.markdown("""
<style>
/* ── Global dark background ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0F0F1A;
    color: #ECECEC;
    font-family: 'Segoe UI', 'Inter', sans-serif;
}

/* ── Header bar ── */
.sim-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 12px;
    padding: 20px 30px;
    margin-bottom: 18px;
    border: 1px solid #2A2A5A;
    display: flex; align-items: center; gap: 14px;
}
.sim-title { font-size: 28px; font-weight: 800; color: #E0E0FF; margin: 0; }
.sim-sub   { font-size: 13px; color: #8888CC; margin: 0; }

/* ── Side panel headings ── */
.panel-trad { border-left: 4px solid #E74C3C; padding-left: 12px; font-size: 17px; font-weight: 700; color: #FF6B6B; }
.panel-lean { border-left: 4px solid #2ECC71; padding-left: 12px; font-size: 17px; font-weight: 700; color: #4ADE80; }

/* ── KPI metric cards ── */
.kpi-row { display: flex; gap: 10px; margin-bottom: 10px; }
.kpi-card {
    background: #1E1E2E; border-radius: 10px; padding: 12px 16px;
    flex: 1; border: 1px solid #2A2A5A; text-align: center;
}
.kpi-value { font-size: 22px; font-weight: 800; }
.kpi-label { font-size: 11px; color: #888; margin-top: 2px; }
.kpi-trad  { color: #E74C3C; }
.kpi-lean  { color: #2ECC71; }

/* ── Log box ── */
.log-box {
    background: #12121F; border-radius: 8px; padding: 10px 12px;
    font-size: 11px; font-family: monospace; color: #CCCCEE;
    height: 200px; overflow-y: auto; border: 1px solid #2A2A5A;
    white-space: pre-wrap; word-break: break-word;
}

/* ── Section divider ── */
.section-divider {
    border: none; border-top: 1px solid #2A2A5A; margin: 20px 0;
}

/* ── Summary panel ── */
.summary-box {
    background: linear-gradient(135deg, #0d0d1a 0%, #1a1a3e 100%);
    border-radius: 14px; padding: 24px 30px; margin-top: 20px;
    border: 2px solid #F1C40F; text-align: center;
}
.summary-title { font-size: 22px; font-weight: 800; color: #F1C40F; margin-bottom: 12px; }
.summary-row   { display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; }
.summary-item  { background: #1E1E2E; border-radius: 10px; padding: 12px 20px; min-width: 160px; }
.summary-item .val { font-size: 26px; font-weight: 800; }
.summary-item .lbl { font-size: 12px; color: #AAA; }

/* ── Control buttons override ── */
div[data-testid="column"] button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: transform 0.1s;
}
div[data-testid="column"] button:hover { transform: scale(1.03); }

/* ── Dataframe styling ── */
[data-testid="stDataFrame"] { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Session state initialisation
# =============================================================================

def _init_state() -> None:
    """Initialise all Streamlit session_state keys if not already set."""
    if "initialised" not in st.session_state:
        metrics  = MetricsLogger()
        gen      = TicketGenerator()
        trad_eng = TraditionalEngine(metrics.traditional)
        lean_eng = LeanEngine(metrics.lean)

        # Register engine queues with the shared generator
        gen.register_queue(trad_eng.queue)
        gen.register_queue(lean_eng.queue)

        st.session_state.metrics  = metrics
        st.session_state.gen      = gen
        st.session_state.trad_eng = trad_eng
        st.session_state.lean_eng = lean_eng

        st.session_state.running     = False
        st.session_state.paused      = False
        st.session_state.initialised = True


_init_state()

# Convenience aliases
metrics:  MetricsLogger    = st.session_state.metrics
gen:      TicketGenerator  = st.session_state.gen
trad_eng: TraditionalEngine = st.session_state.trad_eng
lean_eng: LeanEngine        = st.session_state.lean_eng

# =============================================================================
# Header
# =============================================================================

st.markdown("""
<div class="sim-header">
  <div>
    <p class="sim-title">🎯 IT Helpdesk Simulation: Traditional vs Lean Six Sigma</p>
    <p class="sim-sub">Real-time comparison of ticket resolution performance under identical load conditions</p>
  </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# Control Panel
# =============================================================================

ctrl_cols = st.columns([1.2, 1.2, 1.2, 1.3, 1.3, 3])

with ctrl_cols[0]:
    if st.button("▶ Start", use_container_width=True, type="primary"):
        if not st.session_state.running:
            trad_eng.start()
            lean_eng.start()
            gen.start()
            st.session_state.running = True
            st.session_state.paused  = False

with ctrl_cols[1]:
    if st.button("⏸ Pause", use_container_width=True):
        if st.session_state.running and not st.session_state.paused:
            gen.pause()
            trad_eng.pause()
            lean_eng.pause()
            st.session_state.paused = True
        elif st.session_state.paused:
            gen.resume()
            trad_eng.resume()
            lean_eng.resume()
            st.session_state.paused = False

with ctrl_cols[2]:
    if st.button("🔄 Reset", use_container_width=True):
        # Stop everything and flush state
        gen.stop()
        trad_eng.stop()
        lean_eng.stop()
        time.sleep(0.3)

        # Re-create fresh instances
        new_metrics  = MetricsLogger()
        new_gen      = TicketGenerator()
        new_trad_eng = TraditionalEngine(new_metrics.traditional)
        new_lean_eng = LeanEngine(new_metrics.lean)

        new_gen.register_queue(new_trad_eng.queue)
        new_gen.register_queue(new_lean_eng.queue)

        st.session_state.metrics  = new_metrics
        st.session_state.gen      = new_gen
        st.session_state.trad_eng = new_trad_eng
        st.session_state.lean_eng = new_lean_eng
        st.session_state.running  = False
        st.session_state.paused   = False
        st.rerun()

with ctrl_cols[3]:
    if st.button("⚡ Increase Load", use_container_width=True):
        gen.increase_load()

with ctrl_cols[4]:
    if st.button("🐢 Decrease Load", use_container_width=True):
        gen.decrease_load()

with ctrl_cols[5]:
    status_txt = (
        "🟢 Running" if (st.session_state.running and not st.session_state.paused)
        else "🟡 Paused" if st.session_state.paused
        else "⚫ Idle"
    )
    st.markdown(
        f"**Status:** {status_txt} &nbsp;|&nbsp; "
        f"**Arrival Interval:** `{gen.current_interval}` &nbsp;|&nbsp; "
        f"**Tickets Generated:** `{gen.total_generated}`"
    )

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# =============================================================================
# Live Stats KPI Row
# =============================================================================

trad_snap = metrics.traditional.snapshot()
lean_snap  = metrics.lean.snapshot()

def _kpi_html(label: str, value, css_cls: str) -> str:
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-value {css_cls}">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'</div>'
    )

kpi_col1, kpi_div, kpi_col2 = st.columns([5, 0.1, 5])

with kpi_col1:
    st.markdown('<div class="panel-trad">🔴 Traditional System</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="kpi-row">'
        + _kpi_html("Resolved", trad_snap["total_resolved"], "kpi-trad")
        + _kpi_html("Queue", trad_eng.queue_size, "kpi-trad")
        + _kpi_html("Avg Res (s)", trad_snap["avg_resolution_time"], "kpi-trad")
        + _kpi_html("Reassignments", trad_snap["total_reassignments"], "kpi-trad")
        + _kpi_html("TPM", trad_snap["throughput_per_min"], "kpi-trad")
        + '</div>',
        unsafe_allow_html=True,
    )

with kpi_col2:
    st.markdown('<div class="panel-lean">🟢 Lean Six Sigma System</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="kpi-row">'
        + _kpi_html("Resolved", lean_snap["total_resolved"], "kpi-lean")
        + _kpi_html("Queue", lean_eng.queue_size, "kpi-lean")
        + _kpi_html("Avg Res (s)", lean_snap["avg_resolution_time"], "kpi-lean")
        + _kpi_html("Reassignments", lean_snap["total_reassignments"], "kpi-lean")
        + _kpi_html("TPM", lean_snap["throughput_per_min"], "kpi-lean")
        + '</div>',
        unsafe_allow_html=True,
    )

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# =============================================================================
# Split-Screen: Queue Tables + Logs
# =============================================================================

left_col, right_col = st.columns(2, gap="medium")

with left_col:
    st.markdown("##### 📋 Traditional — Live Queue (top 10)")
    trad_queue_data = trad_eng.get_queue_snapshot()
    if trad_queue_data:
        st.dataframe(
            pd.DataFrame(trad_queue_data),
            use_container_width=True, hide_index=True, height=180
        )
    else:
        st.caption("Queue is empty")

    st.markdown("##### ✅ Traditional — Recently Resolved")
    trad_res = trad_eng.get_resolved_snapshot()
    if trad_res:
        st.dataframe(
            pd.DataFrame(trad_res),
            use_container_width=True, hide_index=True, height=180
        )
    else:
        st.caption("No resolved tickets yet")

    st.markdown("##### 📝 Traditional — Processing Log")
    trad_log = "\n".join(trad_eng.get_log()[::-1])  # newest first
    st.markdown(
        f'<div class="log-box">{trad_log if trad_log else "Waiting for simulation to start…"}</div>',
        unsafe_allow_html=True
    )

with right_col:
    st.markdown("##### 📋 Lean — Live Queue (top 10)")
    lean_queue_data = lean_eng.get_queue_snapshot()
    if lean_queue_data:
        st.dataframe(
            pd.DataFrame(lean_queue_data),
            use_container_width=True, hide_index=True, height=180
        )
    else:
        st.caption("Queue is empty")

    st.markdown("##### ✅ Lean — Recently Resolved")
    lean_res = lean_eng.get_resolved_snapshot()
    if lean_res:
        st.dataframe(
            pd.DataFrame(lean_res),
            use_container_width=True, hide_index=True, height=180
        )
    else:
        st.caption("No resolved tickets yet")

    st.markdown("##### 📝 Lean — Processing Log")
    lean_log = "\n".join(lean_eng.get_log()[::-1])
    st.markdown(
        f'<div class="log-box">{lean_log if lean_log else "Waiting for simulation to start…"}</div>',
        unsafe_allow_html=True
    )

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# =============================================================================
# Comparison Charts (4 charts in 2×2 grid)
# =============================================================================

st.markdown("## 📊 Live Performance Comparison Dashboard")

chart_row1 = st.columns(2, gap="medium")
chart_row2 = st.columns(2, gap="medium")

with chart_row1[0]:
    st.markdown("#### ⏱ Avg Resolution Time")
    fig1 = dash.chart_avg_resolution_time(
        trad_snap["avg_resolution_time"],
        lean_snap["avg_resolution_time"],
    )
    st.pyplot(fig1, use_container_width=True)

with chart_row1[1]:
    st.markdown("#### 🔄 Total Reassignments")
    fig2 = dash.chart_reassignments(
        trad_snap["total_reassignments"],
        lean_snap["total_reassignments"],
    )
    st.pyplot(fig2, use_container_width=True)

with chart_row2[0]:
    st.markdown("#### 🚀 Throughput (tickets/last 60s)")
    fig3 = dash.chart_throughput(
        trad_snap["throughput_per_min"],
        lean_snap["throughput_per_min"],
    )
    st.pyplot(fig3, use_container_width=True)

with chart_row2[1]:
    st.markdown("#### 📈 Queue Size Trend")
    fig4 = dash.chart_queue_size_trend(
        metrics.traditional.queue_size_history,
        metrics.lean.queue_size_history,
    )
    st.pyplot(fig4, use_container_width=True)

# =============================================================================
# Final Summary Panel (appears once SUMMARY_TRIGGER_COUNT tickets are resolved)
# =============================================================================

if metrics.should_show_summary():
    t_avg = trad_snap["avg_resolution_time"]
    l_avg = lean_snap["avg_resolution_time"]
    imp   = metrics.improvement_pct()
    imp_txt = f"{imp:.1f}%" if imp is not None else "N/A"
    imp_colour = "#2ECC71" if (imp is not None and imp > 0) else "#E74C3C"

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(f"""
<div class="summary-box">
  <div class="summary-title">🏆 Performance Summary (after {config.SUMMARY_TRIGGER_COUNT}+ tickets)</div>
  <div class="summary-row">
    <div class="summary-item">
      <div class="val" style="color:#E74C3C">{t_avg:.1f}s</div>
      <div class="lbl">Traditional Avg Time</div>
    </div>
    <div class="summary-item">
      <div class="val" style="color:#2ECC71">{l_avg:.1f}s</div>
      <div class="lbl">Lean Avg Time</div>
    </div>
    <div class="summary-item">
      <div class="val" style="color:{imp_colour}">{imp_txt}</div>
      <div class="lbl">Improvement</div>
    </div>
    <div class="summary-item">
      <div class="val" style="color:#E74C3C">{trad_snap['total_reassignments']}</div>
      <div class="lbl">Trad Reassignments</div>
    </div>
    <div class="summary-item">
      <div class="val" style="color:#2ECC71">0</div>
      <div class="lbl">Lean Reassignments</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("#### 🎯 Improvement Summary Chart")
    if imp is not None:
        fig_sum = dash.chart_improvement_summary(t_avg, l_avg, imp)
        st.pyplot(fig_sum, use_container_width=True)

# =============================================================================
# Auto-refresh loop — rerun the page every REFRESH_INTERVAL_MS milliseconds
# =============================================================================

# Use streamlit's built-in auto-refresh via st_autorefresh if available;
# fall back to a simple time.sleep + st.rerun() approach.
try:
    from streamlit_autorefresh import st_autorefresh  # type: ignore
    st_autorefresh(interval=config.REFRESH_INTERVAL_MS, key="autorefresh")
except ImportError:
    # streamlit_autorefresh not installed → use a meta-refresh approximation
    refresh_placeholder = st.empty()
    if st.session_state.running and not st.session_state.paused:
        time.sleep(config.REFRESH_INTERVAL_MS / 1000)
        st.rerun()
