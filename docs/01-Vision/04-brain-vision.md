# Brain Vision 🧠 — The Glass Box

## What Is the Brain?

The Brain is a **real-time 3D neural visualization** of everything happening inside HiveOS. It's not a dashboard — it's a living, breathing representation of your multi-agent system.

```
🧠 HiveOS Brain — LIVE
───────────────────────────────────────────────────────────
    ╭──────────────────────╮
   ╱  ●  ──→  ●  ──→  ●   ╲     ← Agents as neurons
  │   │         │         │   │
  │   ▼         ▼         ▼   │     ← Data flowing
  │  ● ←── ● ←── ●  ──→ ●   │
   ╲  │    ╱╲    │    ╱    ╱
    ╰──●──╯  ╰──●──╯  ╰──╯
       │       │       │
    [Gate]  [Gate]  [Gate]    ← Human touchpoints
───────────────────────────────────────────────────────────
⚡ Activity: HIGH  |  🎯 Active agents: 7/12  |  ⏱️ 2.3s
```

---

## Why "Glass Box"?

Most AI systems are **black boxes** — input goes in, output comes out, and nobody knows what happened in between.

The Brain makes HiveOS a **glass box**:
- Every thought is visible
- Every decision is traceable
- Every step is explainable
- Every fork is shown with context
- Every human approval/rejection is logged

**If an agent makes a mistake, you see exactly why and how.**

---

## Core Visualizations

### 1. Neural Network View

The primary view — agents as neurons in a brain:

| Visual Element | Meaning |
|---------------|---------|
| 🌐 Glowing sphere | An AI agent (neuron) |
| Sphere size | Agent load / importance |
| Sphere color | Agent status (green=idle, blue=working, yellow=awaiting, red=error) |
| Pulse intensity | Current activity level |
| 🔗 Connecting tube | Data/communication channel |
| Tube brightness | Bandwidth usage |
| ✨ Traveling particle | Data/message flowing between agents |
| 💡 Flash on node | Decision being made |
| ⚡ Spark | Error / anomaly |
| 🔒 Lock icon | Awaiting human approval |
| ✅ Checkmark | Human approved |
| ❌ Cross | Human rejected |

### 2. Decision Path Tracing

When you click on a finished flow or agent:

```
Decision Path: Monthly Close #142
┌────────────────────────────────────────────┐
│ Trigger: Manual (by Hossein)              │
│ ├─→ financial-recorder                    │
│ │   ├─→ 142 journal entries processed     │
│ │   ├─→ Trial balance: OK                 │
│ │   └─→ Closing entries: 34 posted        │
│ ├─→ ⏸️ APPROVAL GATE (Variance check)     │
│ │   ├─→ Variance found: 7.2%             │
│ │   ├─→ Escalated to: CFO                 │
│ │   ├─→ Decision: APPROVED with note      │
│ │   │   "Foreign exchange adjustment OK" │
│ │   └─→ Time to decision: 4m 12s         │
│ ├─→ financial-reporter                    │
│ │   ├─→ Income Statement: done            │
│ │   ├─→ Balance Sheet: done              │
│ │   └─→ Cash Flow: done                  │
│ └─→ financial-orchestrator                │
│     └─→ Close report: delivered          │
├── Total time: 12m 34s                     │
├── Agents involved: 3                       │
├── Human approvals: 1 (4m 12s delay)       │
└── Status: ✅ Complete                     │
```

### 3. System Health Neural View

```
🧠 BRAIN STATUS ──────────────────────────────────────────
  ┌─────────────────────────────────────────────────────┐
  │  [💚💚💚💚💚💚💚💛💛❤️]  System Load: 72%          │
  │  [💚💚💚💚💚💚💚💚💚💚]  Agents Online: 12/12     │
  │  [💚💚💚💚💚💚💚💚💚💚]  Flows Today: 47/47       │
  │  [💚💚💚💚❤️❤️❤️❤️❤️❤️]  Errors: 2 (in last hour)  │
  └─────────────────────────────────────────────────────┘
```

### 4. Approval Gate Dashboard

```
⏸️ PENDING APPROVALS ─────────────────────────────────────
┌──────────────────────────────────────────────────────────┐
│ 🔒 Monthly Close #142 — Variance 7.2%                   │
│    Waiting for: CFO (escalated in 2m 14s)               │
│    Context: Foreign exchange adjustment (EUR/IRR)       │
│    [View Details]  [Approve]  [Reject]  [Modify]        │
├──────────────────────────────────────────────────────────┤
│ 🔒 Tax Return #89 — Unusual deduction                   │
│    Waiting for: Tax Manager (3m 45s)                    │
│    Context: R&D deduction > threshold                   │
│    [View Details]  [Approve]  [Reject]  [Modify]        │
└──────────────────────────────────────────────────────────┘
```

---

## Technical Architecture

```
┌────────────────────────────────────────────────────────┐
│              BRAIN SERVER (FastAPI + WebSocket)        │
│                                                         │
│  /api/brain/                                            │
│    ├── WS /stream       → real-time neural data        │
│    ├── GET /state       → current brain state snapshot │
│    ├── GET /decision/{id} → decision path trace        │
│    └── GET /health      → system health neural view    │
│                                                         │
│  Brain Data Pipeline:                                    │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐           │
│  │  Agent  │→ │  Event   │→ │  Brain      │→ WebSocket │
│  │Registry │  │  Stream  │  │  Aggregator │→ REST      │
│  └─────────┘  └──────────┘  └─────────────┘           │
│       ↑            ↑              ↑                     │
│  real-time     audit trail    system metrics            │
└────────────────────┬───────────────────────────────────┘
                     │ WebSocket
┌────────────────────▼───────────────────────────────────┐
│              BRAIN UI (Three.js / WebGL)               │
│                                                         │
│  - Neural network 3D rendering                         │
│  - Particle physics for data flow                      │
│  - Interactive camera (orbit, zoom, focus)             │
│  - Click agent → inspect details                       │
│  - Decision path overlay                                │
│  - Approval gate UI                                     │
│  - Real-time updates via WebSocket                     │
└────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

| Phase | What | Priority |
|-------|------|----------|
| P7.1 | **Event Stream** — Agent lifecycle events pipeline | High |
| P7.2 | **Decision Tracer** — Trace every decision path | High |
| P7.3 | **Approval Gate Engine** — Human-in-loop system | High |
| P7.4 | **Brain API** — REST + WebSocket endpoints | Medium |
| P7.5 | **3D Neural Visualization** — Three.js canvas | Medium |
| P7.6 | **Real-time Updates** — WebSocket data streaming | Medium |
| P7.7 | **Interactive Exploration** — Click, zoom, inspect | Low |
| P7.8 | **Historical Replay** — Watch past executions | Low |

---

## Integration with Playground

```
User in Playground:
    ┌── Designs flow visually ──┐
    │                            │
    ▼                            ▼
[▶ Run Flow] → [🧠 Brain shows live neural activity]
                   │
                   ├─ Agents lighting up as they work
                   ├─ Data particles flowing between them
                   ├─ ⏸️ Gate hits → Brain shows lock
                   ├─ User approves → Lock opens, flow continues
                   └─ Flow done → Brain shows full path traced
```

The Playground and Brain are **two views of the same system**:
- Playground = **what's happening** (design + exec)
- Brain = **how it's happening** (visualization + transparency)
