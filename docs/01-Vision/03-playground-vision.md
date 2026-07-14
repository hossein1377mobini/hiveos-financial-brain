# Playground Vision 🎮

## What Is the Playground?

The Playground is the **interactive flow construction environment** — where users design, configure, run, and monitor multi-agent workflows without touching a single YAML file. It's the bridge between "domain knowledge" and "running agent system."

Think of it as **VS Code + Postman for multi-agent systems**.

---

## Core Capabilities

### 1. Visual Flow Builder (Canvas)

A drag-and-drop canvas where:
- **Nodes** = Agents (with their role, skills, knowledge)
- **Edges** = Dependencies & data flow between agents
- **Triggers** = Start conditions (manual, cron, event, file watch)
- **Gates** = Human approval checkpoints
- **Conditions** = Branching logic (if/else, switch)
- **Loops** = Iterative processing
- **Parallel forks** = Concurrent agent execution

```
[Trigger] → [Agent A] → [Approval Gate] → [Agent B] ──→ [Output]
                │                              │
                └──→ [Agent C (parallel)] ─────┘
```

#### Standard Flow Components (from automation standards):

| Component | Description |
|-----------|-------------|
| **Trigger** | What starts the flow (manual, schedule, webhook, event) |
| **Task** | A single agent action |
| **Condition** | If/else branch based on data |
| **Switch** | Multi-branch routing |
| **Loop** | Repeat until condition met |
| **Parallel** | Run multiple agents simultaneously |
| **Join** | Wait for all parallel branches |
| **Approval Gate** | Human must approve/reject before proceeding |
| **Timer** | Wait/delay between steps |
| **Subflow** | Nest another flow as a step |
| **Error Handler** | What happens on failure (retry, skip, abort, notify) |
| **Transform** | Map/transform data between agents |
| **Decision** | AI-driven routing (let system decide next step) |

### 2. Auto-Agent Generation

This is the **magic feature**. When a user selects a domain and describes their task:

```
User: "I need to close the monthly books"

System:
1. Recognizes domain = "accounting"
2. Parses task → matches to "financial-close" workflow
3. Auto-selects agents: financial-recorder → financial-reporter → financial-orchestrator
4. Sets up dependencies and data flow automatically
5. Presents to user for customization
```

**How it works:**
- Domain knowledge tree maps tasks → required capabilities
- Agent blueprints define skills, inputs, outputs, triggers
- Flow templates provide pre-built orchestrations
- System composes custom flows from matching components

### 3. Template Library

Browse, preview, and customize:

```
Templates (Accounting)
├── 📋 Financial Close (بستن حساب)
│   ├── Monthly Close
│   ├── Quarterly Close
│   └── Year-End Close
├── 📋 Tax Return (اظهارنامه مالیاتی)
│   ├── Corporate Tax
│   ├── VAT Return
│   └── Personal Tax
├── 📋 Audit Engagement (حسابرسی)
│   ├── Internal Audit
│   └── External Audit
├── 📋 Company Valuation (ارزش‌گذاری)
├── 📋 Annual Budget (بودجه)
└── 📋 Fraud Investigation (تقلب)
```

Each template shows:
- Flow diagram preview
- Agent list with roles
- Estimated execution time
- Required inputs/outputs
- Customization options

### 4. Flow Configuration Panel

When a user selects an agent or gate in the canvas:

**Agent Configuration:**
- Agent ID & name
- Skills to activate
- Knowledge paths to load
- Retry policy (count, backoff)
- Timeout setting
- Input mapping (which previous outputs → which inputs)
- Output specification

**Approval Gate Configuration:**
- What triggers the gate (condition expression)
- Who must approve (role, user, or any)
- Notification channel (dashboard, email, Telegram)
- Timeout if no response (auto-approve/reject)
- Escalation path if timeout

**Condition Configuration:**
- Expression builder (visual or code)
- Then/Else branches
- Multiple conditions (AND/OR)

### 5. Run & Debug Mode

When a flow executes:

```
┌─ Execution: Financial Close ─────────────────────────────┐
│                                                           │
│  [✅] financial-recorder  ─── Journal entries done        │
│  [▶] financial-reporter   ─── Running... (trial balance) │
│  [⏳] financial-orchestrator ─── Waiting...               │
│                                                           │
│  Live Log:                                                 │
│  10:32:01 → financial-recorder: Processing journal entries│
│  10:32:05 → financial-recorder: 142 entries reconciled    │
│  10:32:08 → financial-recorder: Closing entries posted   │
│  10:32:10 → financial-reporter: Preparing trial balance  │
│  10:32:12 ⏸️ APPROVAL NEEDED: Trial balance variance >5%  │
│              Review and approve to continue               │
│              [Approve] [Reject] [Modify]                  │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

**Features:**
- Real-time progress per agent
- Live streaming logs
- Approval gate notifications with context
- Pause/resume execution
- Step-through mode (execute one agent at a time)
- Error preview with suggested fixes

### 6. Output & Artifacts

After execution:
- Final output display
- Intermediate artifacts browser
- Execution trace (who did what, when)
- Performance metrics
- Audit-ready report

---

## UI Concept

```
┌──────────────────────────────────────────────────────────────┐
│  HiveOS Playground  [Accounting ▼]  [🔍 Search templates]   │
├────────────┬─────────────────────────────────────────────────┤
│   Toolbox  │   Canvas (drag & drop area)                     │
│            │                                                 │
│  ┌──────┐  │   [Trigger] → [Recorder] → [Gate?] → [Report] │
│  │Agent │  │        │                           │           │
│  ├──────┤  │        └──→ [Analyst] ─────────────┘           │
│  │ Gate │  │                                                 │
│  ├──────┤  │   ┌──────────────────────────────────────┐      │
│  │Cond. │  │   │ Gate: Variance Check                  │      │
│  ├──────┤  │   │ Condition: balance_diff > 5%          │      │
│  │Timer │  │   │ Approver: CFO or Chief Accountant    │      │
│  ├──────┤  │   └──────────────────────────────────────┘      │
│  │Event │  │                                                 │
│  └──────┘  │                                                 │
│            │                                                 │
├────────────┴─────────────────────────────────────────────────┤
│  [▶ Run] [⏸ Pause] [🔍 Validate] [💾 Save As Template]      │
│  [📋 Run History] [📊 Metrics] [🧠 View in Brain]             │
└──────────────────────────────────────────────────────────────┘
```

---

## Technical Architecture

```
┌────────────────────────────────────────────────────────┐
│              PLAYGROUND (Browser)                      │
│  Canvas.js (custom) or React Flow library              │
│  Monaco Editor (YAML editor)                           │
│  WebSocket → live execution feed                       │
└────────────────────┬───────────────────────────────────┘
                     │ REST API + WebSocket
┌────────────────────▼───────────────────────────────────┐
│              PLAYGROUND SERVER (FastAPI)               │
│  /api/playground/                                      │
│    ├── POST /validate         → validate flow YAML     │
│    ├── POST /auto-agents      → auto-gen agent team    │
│    ├── POST /run              → execute flow           │
│    ├── POST /run/{id}/approve → approve gate           │
│    ├── POST /run/{id}/reject  → reject gate            │
│    ├── GET  /run/{id}/status  → streaming status       │
│    └── GET  /run/{id}/log     → streaming logs         │
│  /api/templates/                                       │
│    ├── GET  /                 → list templates         │
│    ├── GET  /{id}             → get template detail    │
│    └── POST /{id}/customize   → customize template     │
└────────────────────┬───────────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────────┐
│              HIVEOS CORE                               │
│  Flow Engine • Agent Registry • Domain Manager         │
│  RBAC • Audit • Workspace • License                    │
└────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

| Phase | What | Priority |
|-------|------|----------|
| P6.1 | **Flow Validator API** — Validate YAML flows via REST | High |
| P6.2 | **Auto-Agent API** — Task → domain agents mapping | High |
| P6.3 | **Template Browser** — Browse, preview domain templates | High |
| P6.4 | **Visual Canvas** — Drag & drop flow builder | High |
| P6.5 | **Run/Debug with streaming** — Execute + live logs | High |
| P6.6 | **Approval Gates UI** — Human-in-loop in dashboard | Medium |
| P6.7 | **Template Customizer** — Clone & edit templates | Medium |
| P6.8 | **Flow Library** — Save, version, share user flows | Medium |
| P6.9 | **Advanced Conditions** — Visual expression builder | Low |
| P6.10 | **Subflows & Nesting** — Compose complex workflows | Low |
