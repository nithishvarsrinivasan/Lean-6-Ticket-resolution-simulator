# =============================================================================
# config.py — Central Configuration for LSS Helpdesk Simulation
# =============================================================================
# All tunable parameters live here. Do NOT hardcode values in other modules.
# =============================================================================

# --------------- Ticket Generation ---------------
TICKET_ARRIVAL_MIN_SEC   = 1.0   # Minimum simulated arrival gap (seconds real-time)
TICKET_ARRIVAL_MAX_SEC   = 3.0   # Maximum simulated arrival gap (seconds real-time)

# Issue types available for ticket generation
ISSUE_TYPES = ["Network", "Software", "Hardware", "Access", "Security"]

# Departments tickets can originate from
DEPARTMENTS = ["Finance", "HR", "IT", "Operations", "Sales", "Engineering"]

# Priority distribution weights (must sum to 1.0)
PRIORITY_WEIGHTS = {
    "High":   0.20,
    "Medium": 0.50,
    "Low":    0.30,
}

# --------------- Traditional Engine Timings (seconds, real-time) ---------------
TRAD_CLASSIFICATION_MIN  = 5    # Min classification delay
TRAD_CLASSIFICATION_MAX  = 12   # Max classification delay
TRAD_WRONG_ASSIGN_PROB   = 0.40 # Probability of wrong assignment (40%)
TRAD_REASSIGN_DELAY      = 6    # Delay per reassignment (seconds)
TRAD_RESOLUTION_MIN      = 5    # Min resolution delay
TRAD_RESOLUTION_MAX      = 15   # Max resolution delay

# --------------- Lean Engine Timings (seconds, real-time) ---------------
LEAN_CLASSIFICATION_DELAY = 1   # Automated classification (fixed)
LEAN_RESOLUTION_MIN       = 5   # Min resolution delay
LEAN_RESOLUTION_MAX       = 10  # Max resolution delay

# --------------- Lean Routing Rules ---------------
# Maps issue type → responsible team
LEAN_ROUTING = {
    "Network":  "Infra Team",
    "Software": "App Team",
    "Hardware": "Device Team",
    "Access":   "IAM Team",
    "Security": "Security Team",
}

# Traditional teams (random pool)
TRADITIONAL_TEAMS = [
    "Team Alpha", "Team Beta", "Team Gamma",
    "Team Delta", "Team Epsilon"
]

# --------------- Metrics ---------------
SUMMARY_TRIGGER_COUNT = 50   # Show final summary after this many tickets resolved (combined)

# --------------- UI / Visual ---------------
REFRESH_INTERVAL_MS   = 1500   # Streamlit auto-refresh interval in milliseconds
MAX_LOG_DISPLAY       = 20     # Max log entries shown per panel

# Status colour labels (used in dashboard tables)
STATUS_COLORS = {
    "Pending":    "🟡 Pending",
    "Processing": "🔵 Processing",
    "Resolved":   "🟢 Resolved",
    "Reassigned": "🔴 Reassigned",
}

# --------------- Ticket Load Control ---------------
LOAD_STEP = 0.5   # Seconds to add/remove from arrival interval per load change
LOAD_MIN  = 0.5   # Minimum arrival interval (fastest load)
LOAD_MAX  = 5.0   # Maximum arrival interval (slowest load)
