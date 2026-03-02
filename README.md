# Lean Six Sigma Ticket Resolution Simulator

## Project Overview

This project is an interactive simulation designed to demonstrate the performance difference between:

1. **Traditional Help Desk Ticket System**
2. **Lean Six Sigma Optimized Ticket System**

Both systems receive identical incoming ticket requests and process them using different operational strategies. The simulation visually and quantitatively compares performance metrics in real-time.

This project supports **Lean Six Sigma (DMAIC) validation** by providing measurable evidence of process improvement.

---

## Purpose

The goal of this simulator is to:

- Demonstrate process variation in traditional systems
- Show the impact of standardized triage
- Quantify waste reduction
- Validate measurable improvement
- Support Lean Six Sigma Review-2 presentation

---

## System Architecture

```
User Ticket Generator
          ↓
   Shared Ticket Queue
      ↓           ↓
Traditional    Lean System
  Engine         Engine
      ↓           ↓
 Metrics Logger (Separate Tracking)
          ↓
   Comparison Dashboard
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| UI Framework | Streamlit |
| Visualization | Matplotlib |
| Concurrency | Threading / Async processing |
| Design | Modular architecture |

---

##  Project Structure

```
project/
│
├── main.py                 
├── ticket_generator.py     
├── traditional_engine.py   
├── lean_engine.py          
├── metrics.py              
├── dashboard.py            
├── config.py               
└── README.md
```

---

## Ticket Structure

Each generated ticket contains:

| Field | Description |
|-------|-------------|
| `id` | Unique ticket identifier |
| `issue_type` | Network, Software, Hardware, Access, or Security |
| `priority` | High (20%), Medium (50%), or Low (30%) |
| `timestamp` | Time of ticket creation |
| `assigned_team` | Team routed to handle the ticket |
| `resolution_time` | Time taken to resolve (seconds) |
| `reassignments` | Number of times the ticket was re-routed |

Tickets are generated every **1–3 seconds** with randomized categories and priority distribution.

---

## Traditional System Logic

Simulates real-world inefficiencies:

- Manual categorization delay: **5–12 seconds** (simulated)
- Random team assignment with no deterministic logic
- **40% probability** of wrong routing
- Reassignment delay: **6 seconds** per mis-routed ticket
- Resolution time: **5–15 seconds**
- Tracks full reassignment count per ticket

**Lean Waste Demonstrated:**

| Waste Type | Manifestation |
|------------|---------------|
| Waiting | Manual categorization delay |
| Rework | Ticket reassignment after wrong routing |
| Motion | Tickets moving between wrong teams |
| Process Variation | Inconsistent resolution times per agent |

---

## Lean Six Sigma System Logic

Simulates an optimized triage process:

- Rule-based automatic categorization
- Direct routing to the correct team (deterministic)
- Classification delay: **1 second**
- **Zero reassignments**
- Resolution time: **5–10 seconds**

**Lean Principles Applied:**

| Principle | Implementation |
|-----------|----------------|
| Standardized Work | Rule-based triage engine (`lean_engine.py`) |
| Waste Elimination | No reassignments, no manual delays |
| Flow Improvement | Direct routing, reduced queue buildup |
| Variation Reduction | Consistent categorization logic |
| Control Monitoring | Live metrics tracked per ticket |

---

## Metrics Tracked

Tracked independently for both systems:

- Average resolution time
- Total tickets processed
- Reassignment count
- Average waiting time
- Throughput per minute
- Queue size

---

## Dashboard Features

### Split View Layout
- **Left Panel** → Traditional System
- **Right Panel** → Lean Six Sigma System

### Live Data Display
- Real-time ticket queues (top 10)
- Processing logs with timestamps
- Resolved ticket counts

### Comparison Charts
| Chart | Description |
|-------|-------------|
| Avg Resolution Time | Side-by-side bar comparison |
| Total Reassignments | Cumulative reassignment count |
| Throughput | Tickets resolved per minute |
| Queue Size Trend | Queue depth over elapsed time |

---

## Control Panel

| Button | Action |
|--------|--------|
| Start | Begin the simulation |
| Pause | Pause ticket generation and processing |
| Reset | Clear all metrics and restart |
| Increase Load | Reduce ticket arrival interval |
| Decrease Load | Increase ticket arrival interval |

---

## How to Run

### Install Dependencies

```bash
pip install streamlit matplotlib
```

### Run Application

```bash
streamlit run main.py
```

---

##  Related

This simulator was built to support a **Lean Six Sigma DMAIC project** focused on IT Help Desk Ticket Resolution Time reduction for academic course Lean Six Sigma Principles
