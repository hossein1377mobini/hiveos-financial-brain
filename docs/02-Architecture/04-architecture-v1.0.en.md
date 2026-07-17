# HiveOS v1.0 Architecture — Operating System for Business AI Agents

> **Version:** v0.12 (Architecture Draft)
> **Date:** July 2026
> **Author:** HiveOS Architecture Team
> **Audience:** Developers, System Architects, Technical Investors

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Kernel](#3-kernel)
4. [Planner](#4-planner)
5. [Workflow Runtime](#5-workflow-runtime)
6. [Memory Model](#6-memory-model)
7. [Event Bus](#7-event-bus)
8. [Tool Bus](#8-tool-bus)
9. [Domain SDK](#9-domain-sdk)
10. [Plugin API](#10-plugin-api)
11. [Bridge to Future Versions](#11-bridge-to-future-versions)
12. [Architecture Decision Records](#12-architecture-decision-records)

---

## 1. Executive Summary

### What is HiveOS?

HiveOS is an **Operating System for Business AI Agents**. Just as Linux provides fundamental services to applications (filesystem, networking, memory), HiveOS provides fundamental services to AI agents: memory, planning, execution, learning, and communication.

### Current Status

The project is at **v0.11.1** with the following layers built:

| Layer | Status | Description |
|-------|--------|-------------|
| **Flow Engine** | ✅ | Sequential and DAG-based workflow execution |
| **Mothership** | ✅ | Central server for agent registration, task routing, communication |
| **Enterprise** | ✅ | RBAC, Audit Trail, Multi-tenant, Pricing |
| **Brain** | ✅ | Event Stream, Decision Tracer, Approval Gate |
| **Playground** | ✅ | Visual Canvas, Component Engine with 10 component types |
| **Learning** | ✅ | Execution Logger, Analytics, Pattern Recognition |
| **Storage** | ✅ | SQLite-based StorageEngine |
| **Domain Registry** | ✅ | Domain registration, discovery, learning |
| **Desktop** | ✅ | Native Windows shell (pywebview) + PWA |
| **Accounting Domain** | ✅ | 29 agents, 6 flows, 480+ knowledge files |
| **Agent Learning** | ✅ | 24 documentation files (~300KB) |

**436 tests** — all passing.

### The Gap

What doesn't exist yet: **Runtime** and **Planner**. Currently, agents call tools directly or execute simple flows. But the system still lacks:

- **Workflow as a first-class entity** (save/resume/pause/schedule)
- **Planning before execution** (goal decomposition, capability matching)
- **Systematic reflection** (learning from executions)
- **Company Memory** (organizational knowledge shared across agents)

This architecture document defines the roadmap from current state to v1.0.

---

## 2. System Overview

### 2.1 Design Philosophy

HiveOS is built on 5 architectural principles:

| Principle | Description | Example |
|-----------|-------------|---------|
| **1. Kernel Minimalism** | The kernel has minimal responsibility | Kernel doesn't plan — it runs the Planner |
| **2. Everything is a Plugin** | Everything is added through Plugin API | Domains, Agents, Tools, even Runtime |
| **3. Event-Driven** | Everything communicates through events | No component directly calls another |
| **4. Memory First** | Memory is a first-layer concern, not an add-on | Every decision is recorded in memory |
| **5. Human in the Loop** | Humans can always intervene | Approval Gate at every decision point |

### 2.2 Seven Layers

HiveOS v1.0 architecture consists of 7 layers. Important: these layers are **not release versions** — releases are **evolution horizons**, each maturing one layer.

```
                    ┌─────────────────────────────────┐
                    │        Domain SDK (Layer 7)      │
                    │  Developer tools for building     │
                    │  new domains                     │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │       Plugin API (Layer 6)        │
                    │     Third-party extensions        │
                    └────────────────┬────────────────┘
                                     │
┌────────────────────────────────────────────────────────────────────┐
│                    ┌───────────────┐  ┌───────────────┐            │
│                    │   Planner    │  │   Runtime    │  Layers 4&5 │
│                    └───────┬───────┘  └───────┬───────┘            │
│     ┌──────────────────────┴──────────────────┴──────────────┐   │
│     │                    Tool Bus (Layer 3)                    │   │
│     └──────────────────────────┬──────────────────────────────┘   │
│                                │                                  │
│     ┌──────────────────────────▼──────────────────────────────┐   │
│     │          Event Bus (Layer 2) — System Backbone           │   │
│     └──────────────────────────┬──────────────────────────────┘   │
│                                │                                  │
│     ┌──────────────────────────▼──────────────────────────────┐   │
│     │   Memory Model (Layer 1)                                 │   │
│     │   Session · Agent · Domain · Company · Long-Term        │   │
│     └──────────────────────────┬──────────────────────────────┘   │
│                                │                                  │
│     ┌──────────────────────────▼──────────────────────────────┐   │
│     │            Kernel (Layer 0)                              │   │
│     │     StorageEngine · Config · Logging · Lifecycle        │   │
│     └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### 2.3 Naming Convention

| Entity | Convention | Example |
|--------|-----------|---------|
| **Version** | Semantic Versioning | v0.12.0, v1.0.0 |
| **Domain** | kebab-case | `accounting`, `tax-iran` |
| **Agent Blueprint** | kebab-case | `financial-analyst` |
| **Tool** | kebab-case | `financial-statement-reader` |
| **Flow** | kebab-case | `tax-calculation-flow` |
| **Event Type** | `domain:entity:action` | `flow:step:completed` |
| **Namespace** | `snake_case` | `domain_registry` |
| **JSON Key** | `snake_case` | `installed_at` |

---

## 3. Kernel

### 3.1 Definition

The **Kernel** is the minimal set of services every other component requires to function. The kernel **does not know** what a Planner, Runtime, or Domain is.

### 3.2 Responsibilities

| Service | Responsibility | Current Status |
|---------|---------------|----------------|
| **StorageEngine** | SQLite-based key-value persistence | ✅ Existing |
| **Config Management** | Load configuration from YAML + env | ✅ Partial |
| **Logging** | System event logging | ✅ Existing |
| **Lifecycle Manager** | Graceful component start/stop | ❌ Needs work |
| **Dependency Injection** | Internal service registration/discovery | ❌ Needs work |
| **Health Check** | Kernel self-health monitoring | ❌ Needs work |

### 3.3 Kernel API

```python
class Kernel:
    """
    HiveOS Kernel — a container for fundamental services.
    
    Usage:
        kernel = Kernel(storage=StorageEngine("hiveos.db"))
        kernel.register("memory", MemoryService())
        kernel.register("event_bus", EventBus())
        
        await kernel.start()    # Start all services
        await kernel.shutdown() # Graceful stop
    """
    
    def __init__(self, storage: StorageEngine, config: dict = None):
        self.storage = storage
        self.config = config or {}
        self._services: dict[str, Service] = {}
        self._lifecycle: LifecycleManager = LifecycleManager()
    
    def register(self, name: str, service: Service):
        """Register a service with the kernel"""
        self._services[name] = service
    
    def get(self, name: str) -> Service:
        """Access a registered service"""
        return self._services[name]
    
    async def start(self):
        """Start all services in dependency order"""
        for name, svc in self._topological_services():
            await svc.start()
    
    async def shutdown(self):
        """Stop all services in reverse order"""
        for name, svc in reversed(self._topological_services()):
            await svc.shutdown()
```

### 3.4 Kernel Boundaries

**The kernel does:** storage, service registration, lifecycle management, logging.

**The kernel does NOT do:**
- Planning → that's the Planner's job
- Workflow execution → that's the Runtime's job
- Intelligent memory → that's the Memory Service
- Message routing → that's the Event Bus
- Tool management → that's the Tool Bus

---

## 4. Planner

### 4.1 Why Planner Before Runtime?

Question: Why build the **Planner first**, then Runtime?

Answer: Because the Runtime must **execute a Plan**, not decide what to do on its own. If we build Runtime without Planner, we get the same simple execution engine we have now — just with better state management. A Runtime designed to execute Plans is **fundamentally different** from one that calls agents directly.

**Runtime with vs without Planner:**

| Feature | Runtime w/o Planner | Runtime with Planner |
|---------|-------------------|---------------------|
| **Input** | "Do this task" | A structured DAG-based Plan |
| **Decision-making** | Runtime decides how to execute | Plan has pre-made decisions |
| **Error Recovery** | Limited (mostly retry) | Can modify plan or replan |
| **Auditability** | Medium (logging) | Full (every decision in plan) |
| **Optimization** | Hard | Compare different plans |

### 4.2 Planner Architecture

```
User Goal (e.g., "Analyze Company X's financial health for investment")
    │
    ▼
┌─────────────────────────────────────────────┐
│              Planner                         │
│                                              │
│  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Goal Analyzer   │  │  Decomposition   │  │
│  │  (vague → clear) │──│  (goal → tasks)  │  │
│  └──────────────────┘  └────────┬─────────┘  │
│                                 │            │
│  ┌──────────────────────────────▼──────────┐ │
│  │  Capability Matcher                     │ │
│  │  Match tasks to available agents        │ │
│  └──────────────────────────┬──────────────┘ │
│                             │                │
│  ┌──────────────────────────▼──────────────┐ │
│  │  Dependency Resolver                    │ │
│  │  Determine execution order (DAG)        │ │
│  └──────────────────────────┬──────────────┘ │
│                             │                │
│  ┌──────────────────────────▼──────────────┐ │
│  │  Plan Validator                         │ │
│  │  Is the plan executable?               │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  Output: ExecutionPlan (complete DAG)        │
└─────────────────────────────────────────────┘
    │
    ▼
ExecutionPlan → Runtime
```

### 4.3 Three Levels of Planning

The Planner has three levels, selected based on **complexity** and **uncertainty** of the goal:

```
High Complexity ▲
                 │
                 │    Level 3: Strategic Planning
                 │    (LLM-intensive, dynamic revision)
                 │
                 │    Level 2: Template-Based Planning
                 │    (pre-defined flow templates)
                 │
                 │    Level 1: Immediate Planning
                 │    (simple tasks, single agent)
                 └───────────────────────────────► High Uncertainty
```

#### Level 1 — Immediate Planning

For simple tasks requiring one agent:

```yaml
# Input: "Check stock price of X"
execution_plan:
  type: immediate
  agents:
    - id: market-researcher
      task: "Check price of stock X"
      tools: [stock-api, web-search]
  output: "Stock price report"
```

**LLM cost:** Very low (zero — just agent selection)
**Execution time:** < 1 second

#### Level 2 — Template-Based Planning

For repetitive tasks with existing Flow templates:

```yaml
# Input: "Calculate payroll tax for employee 12345"
execution_plan:
  type: template-based
  template: payroll-tax-calculation
  parameters:
    employee_id: "EMP-12345"
    month: "Farvardin"
    year: 1404
  agents:
    - id: salary-calculator
      task: "Calculate gross salary"
      tools: [hr-system-api, attendance-system]
    - id: tax-calculator
      depends_on: [salary-calculator]
      task: "Calculate income tax per 1404 table"
      tools: [tax-table-1404, deduction-calc]
    - id: insurance-calculator
      depends_on: [salary-calculator]
      task: "Calculate social insurance"
      tools: [insurance-table-1404]
    - id: payslip-generator
      depends_on: [tax-calculator, insurance-calculator]
      task: "Generate payslip"
      tools: [payslip-template]
```

**LLM cost:** Low (parameter filling only)
**Execution time:** < 5 seconds

#### Level 3 — Strategic Planning

For complex, long-term goals:

```yaml
# Input: "Prepare a comprehensive financial health analysis of Company X for investment"
execution_plan:
  type: strategic
  goal: "Financial health analysis of Company X"
  
  decomposition_strategy: llm-guided
  max_depth: 3
  max_branches: 5
  
  checkpoint: true
  human_review_points:
    - after financial section
    - before final recommendation
  
  phases:
    - phase: 1
      name: "Data Collection"
      parallel:
        - agent: financial-scraper
          task: "Get 3 years of financial statements"
        - agent: market-researcher
          task: "Industry and competitor analysis"
        - agent: news-analyzer
          task: "Legal and reputational risk check"
    
    - phase: 2
      name: "Analysis"
      depends_on: [phase-1]
      agents:
        - agent: ratio-analyzer
          task: "Calculate and interpret financial ratios"
          input_from: [financial-scraper]
        - agent: risk-assessor
          task: "Operational and financial risk assessment"
          input_from: [news-analyzer, market-researcher]
    
    - phase: 3
      name: "Final Report"
      depends_on: [phase-2]
      agents:
        - agent: report-writer
          task: "Compile investment report"
          input_from: [ratio-analyzer, risk-assessor]
        - agent: reviewer
          task: "Quality and accuracy review"
```

**LLM cost:** Medium to high (decomposition + each agent)
**Execution time:** 30 seconds to 5 minutes

### 4.4 ExecutionPlan Data Structure

```json
{
  "plan_id": "plan_abc123",
  "goal": "Financial analysis of Company X",
  "type": "strategic",
  "created_at": "2026-07-20T10:00:00Z",
  "status": "ready",
  
  "phases": [
    {
      "id": "phase-1",
      "name": "Data Collection",
      "parallel": true,
      "agents": [
        {
          "agent_id": "financial-scraper",
          "domain": "accounting",
          "task": "Get financial statements",
          "tools": ["web-scraper", "pdf-extractor"],
          "expected_output": "structured_financial_data",
          "timeout": 120
        }
      ],
      "depends_on": []
    }
  ],
  
  "variables": {
    "input": {"company": "X"},
    "intermediate": {},
    "output": {}
  },
  
  "human_review_points": ["phase-2/output"],
  "metadata": {
    "total_agents": 7,
    "estimated_duration": 180,
    "llm_cost_estimate": 0.15
  }
}
```

### 4.5 Planner Implementation Path

| Step | Work | Estimate |
|------|------|----------|
| 1 | `Planner` class with Immediate mode | 1 day |
| 2 | Template matcher (Level 2) | 2 days |
| 3 | LLM-guided decomposition (Level 3) | 3 days |
| 4 | Plan Validator (DAG, cycle detection) | 1 day |
| 5 | Plan storage + history | 1 day |
| 6 | API endpoints | 1 day |
| 7 | Desktop UI for Plan display | 2 days |
| 8 | Tests | 2 days |
| **Total** | | **13 days** |

---

## 5. Workflow Runtime

### 5.1 Definition

The Runtime is the system that receives an **ExecutionPlan** and **executes, tracks, and manages** it. The Runtime **doesn't know** how the Plan was created — it only executes it.

### 5.2 Runtime vs Current Flow Engine

| Feature | Flow Engine (Current) | Runtime (Target) |
|---------|----------------------|-----------------|
| **Input** | Manual Flow YAML | ExecutionPlan from Planner |
| **State Management** | JSON file-based | StorageEngine + State Machine |
| **Pause/Resume** | ❌ Not supported | ✅ Supported |
| **Schedule** | ❌ Not supported | ✅ Cron + Event + Webhook |
| **HITL** | ❌ Not supported | ✅ Built-in Approval Gate |
| **Parallel** | ❌ Sequential only | ✅ True parallel execution |
| **Error Recovery** | Simple retry | Retry + Skip + Replan + Abort |
| **Observability** | Console log | Event Stream + Metrics |
| **Timeout** | agent-level only | workflow-level + agent-level |

### 5.3 Workflow State Machine

```
     ┌──────────┐
     │  Created │
     └────┬─────┘
          │ Schedule / Trigger
          ▼
     ┌──────────┐
     │  Planned  │
     └────┬─────┘
          │ Execute
          ▼
     ┌──────────┐
     │  Running  │
     └────┬─────┘
          │
     ┌────┴────┐──── ─ ─ ─ ─ ─
     │         │               │
     ▼         ▼               ▼
┌────────┐ ┌────────┐  ┌──────────┐
│Paused  │ │Failed  │  │Completed │
└───┬────┘ └────────┘  └──────────┘
    │ Resume
    ▼
 ┌──────────┐
 │  Running  │
 └──────────┘
```

Possible states:

| State | Meaning | Resumable? |
|-------|---------|------------|
| `created` | Workflow created but not started | — |
| `planned` | ExecutionPlan ready | — |
| `running` | Currently executing | ✅ |
| `paused` | Stopped (manual or HITL) | ✅ |
| `failed` | Failed (after all retries) | ❌ (must replan) |
| `cancelled` | Cancelled by user | ❌ |
| `completed` | Successful | — |
| `completed_with_errors` | Success with some failures | — |

### 5.4 State Persistence

Each Workflow is stored in StorageEngine as follows:

```python
workflow_state = {
    "id": "wf_abc123",
    "plan_id": "plan_def456",
    "status": "running",
    "started_at": "2026-07-20T10:00:00Z",
    "phases": {
        "phase-1": {
            "status": "completed",
            "started_at": "...",
            "completed_at": "...",
            "agents": {
                "financial-scraper": {
                    "status": "completed",
                    "result": "{...}",
                    "token_count": 1500,
                    "duration_ms": 8500
                }
            }
        },
        "phase-2": {
            "status": "running",
            "agents": {
                "ratio-analyzer": {
                    "status": "running",
                    "started_at": "..."
                }
            }
        }
    },
    "variables": {
        "input": {...},
        "phase-1/output": "{...}",
        "phase-2/ratio-analyzer/output": None
    },
    "timeline": [
        {"type": "phase_started", "phase": "phase-1", "at": "..."},
        {"type": "agent_completed", "agent": "financial-scraper", "at": "..."},
        {"type": "phase_completed", "phase": "phase-1", "at": "..."},
    ]
}
```

### 5.5 Trigger Types

The Runtime supports 4 trigger types:

| Trigger | Description | Example |
|---------|-------------|---------|
| **Manual** | User-initiated execution | "Run" button in Dashboard |
| **Cron** | Scheduled execution | "Every day at 8 AM: generate yesterday's report" |
| **Event** | Triggered by an event | "When invoice > 50M is registered: start approval" |
| **Webhook** | Triggered by external HTTP request | "External ERP: new customer registered" |

### 5.6 HITL — Human in the Loop

The Runtime supports pause points for **human approval**:

```yaml
# Inside ExecutionPlan:
human_review_points:
  - id: approve-invoice
    phase: phase-2
    description: "Approve invoice above 50M"
    required_role: "finance-manager"
    timeout: 86400  # 24 hours
    on_timeout: "notify-escalate"
    actions:
      - approve
      - reject
      - modify
```

When the Runtime reaches a HITL point:
1. Pauses the Workflow (→ `paused` state)
2. Creates an ApprovalGate in Brain
3. Sends notification to the relevant user/role
4. Waits for user decision (approve/reject)
5. Resumes execution after decision

### 5.7 Error Handling

The Runtime supports 4 error strategies:

```yaml
error_strategies:
  - type: retry
    max_attempts: 3
    backoff: exponential  # 2s → 4s → 8s
  
  - type: skip
    continue_workflow: true
    mark_as: skipped
  
  - type: replan
    trigger: "runtime_error"
    replan_from: "failed-agent"  # Planner replans from here
  
  - type: abort
    human_notification: true
    fallback_output: "Manual review required"
```

### 5.8 Runtime Implementation Path

| Step | Work | Estimate |
|------|------|----------|
| 1 | State Machine (WorkflowState class) | 1 day |
| 2 | Phase Executor (sequential/parallel) | 2 days |
| 3 | Persistence (StorageEngine) | 1 day |
| 4 | Pause/Resume | 1 day |
| 5 | HITL integration | 2 days |
| 6 | Schedule (cron) | 2 days |
| 7 | Event triggers | 2 days |
| 8 | Error strategies | 2 days |
| 9 | Observability (metrics + events) | 1 day |
| 10 | API endpoints | 1 day |
| 11 | Desktop UI | 2 days |
| 12 | Tests | 3 days |
| **Total** | | **21 days** |

---

## 6. Memory Model

### 6.1 Five Levels of Memory

Memory in HiveOS is not a single layer — it's a **hierarchy**. Each level has a different scope and retention period:

```
Granularity                     Scope
  │                              │
  ▼                              ▼
┌──────────────────────────────────────────────┐
│   Level 5: Long-Term Memory                  │  ▲
│   scope: entire system · retention: forever  │  │
├──────────────────────────────────────────────┤  │
│   Level 4: Company Memory                    │  │
│   scope: entire organization · retention: ∞ │  │
├──────────────────────────────────────────────┤  │
│   Level 3: Domain Memory                     │  │
│   scope: one Domain · retention: until update│  │
├──────────────────────────────────────────────┤  │
│   Level 2: Agent Memory                      │  │
│   scope: one Agent · retention: session      │  │
├──────────────────────────────────────────────┤  │
│   Level 1: Session Memory                    │  │
│   scope: one user interaction · retention: S │  │
└──────────────────────────────────────────────┘  │
                                                  ▼
Retention                         Access Speed
```

### 6.2 Level 1: Session Memory

Instant **chat memory** for user-system interaction:

| Property | Value |
|----------|-------|
| **scope** | One user-system conversation |
| **retention** | Until session end (max 24h) |
| **storage** | In-memory (optional Redis/SQLite) |
| **content** | Message history, current context |
| **API** | `kernel.get("session").push(msg)` |

### 6.3 Level 2: Agent Memory

Each Agent's memory during a Workflow execution:

| Property | Value |
|----------|-------|
| **scope** | One Agent in one Execution |
| **retention** | Agent lifespan (spawn to complete) |
| **storage** | In-memory (partially in StorageEngine) |
| **content** | Previous phase output, dependency results, available tools |
| **API** | `agent.memory.set("key", value)` |

This level currently exists implicitly via `depends_on` and `output_var` in the Flow Engine — but needs to be made explicit.

### 6.4 Level 3: Domain Memory

Specialized memory for **each Domain** — persists across sessions:

| Property | Value |
|----------|-------|
| **scope** | One specific Domain (e.g., accounting) |
| **retention** | Until next domain update |
| **storage** | StorageEngine — separate namespace |
| **API** | `domain.memory.set("tax-rates-1404", {...})` |

Currently partially exists via `DomainRegistry.learn()` but lacks a standard API.

### 6.5 Level 4: Company Memory

**HiveOS's biggest competitive advantage — to be built in v0.16:**

Organizational memory **shared across all Agents and Domains**:

```python
class CompanyMemory:
    """
    Company Memory — policies, rules, past decisions.
    All Agents have read access.
    Only authorized Agents (with specific roles) can write.
    """
    
    def get_policy(self, domain: str, key: str) -> dict:
        """Get organizational policy"""
    
    def get_decision(self, context: str) -> list[dict]:
        """Find similar past decisions"""
    
    def record_decision(self, context: str, decision: dict):
        """Record a new decision for future reference"""
    
    def get_preference(self, domain: str, key: str) -> Any:
        """Get organizational preference"""
```

**Data types stored in Company Memory:**

| Category | Example |
|----------|---------|
| **Policies** | "Invoices above 50M require finance manager approval" |
| **Accounting Rules** | "Depreciation method: straight-line, 5 years" |
| **Preferred Vendors** | "For software, contact Company X first" |
| **Previous Decisions** | "Dec 2024: Company Y removed from vendor list due to delays" |
| **Risk Appetite** | "Max accepted risk in forex: 3% of capital" |
| **Tax Strategy** | "Optimal tax reduction method for tech services" |
| **Organizational Context** | "Company in rapid growth phase — more aggressive investment" |

### 6.6 Level 5: Long-Term Memory

Compressed and aggregated history of the entire system:

| Property | Value |
|----------|-------|
| **scope** | Entire system — all Workflows, all Agents |
| **retention** | Forever (until manual deletion) |
| **storage** | StorageEngine + periodic compression |
| **API** | Historical search, trend analysis |

### 6.7 Memory Access Rules

```
┌─────────────┐  read/write  ┌─────────────────┐
│ Session     │◄────────────►│ User             │
└──────┬──────┘              └─────────────────┘
       │
       │  read
       ▼
┌─────────────┐  read/write  ┌─────────────────┐
│ Agent       │◄────────────►│ Executing Agent  │
└──────┬──────┘              └─────────────────┘
       │
       │  read (from Domain Registry)
       ▼
┌─────────────┐              ┌─────────────────┐
│ Domain      │◄─── write ──│ Domain Admin     │
└──────┬──────┘              └─────────────────┘
       │
       │  read
       ▼
┌─────────────┐              ┌─────────────────┐
│ Company     │◄─── write ──│ Authorized Roles  │
│ Memory      │              └─────────────────┘
└──────┬──────┘                      
       │  read (all)
       ▼
┌─────────────┐
│ Long-Term   │◄─── write ──│ System (auto)
└─────────────┘
```

---

## 7. Event Bus

### 7.1 Why an Event Bus?

In the current state, components either call each other directly (like `FlowEngine → Hermes subprocess`) or are completely unaware of what happens in other components. The Event Bus solves:

1. **Decoupling:** Components only publish events — they don't know who subscribed
2. **Extensibility:** New features just subscribe to existing events
3. **Auditing:** All events stored in Event Store — complete system history

### 7.2 Event Schema

```json
{
  "id": "evt_h3k2j9",
  "type": "runtime:phase:agent:completed",
  "source": "runtime:phase-executor",
  "timestamp": "2026-07-20T10:00:15.123Z",
  "workflow_id": "wf_abc123",
  "correlation_id": "plan_def456",
  "payload": {
    "agent_id": "financial-scraper",
    "phase": "phase-1",
    "status": "completed",
    "duration_ms": 8500,
    "result_summary": "Financial statements extracted for 3 years"
  },
  "metadata": {
    "token_cost": 1500,
    "model": "claude-sonnet-4"
  }
}
```

Event naming conventions:

| Pattern | Example |
|---------|---------|
| `system:*` | `system:startup`, `system:shutdown` |
| `kernel:*` | `kernel:service:registered`, `kernel:service:failed` |
| `planner:*` | `planner:plan:created`, `planner:plan:rejected` |
| `runtime:*` | `runtime:workflow:started`, `runtime:phase:completed` |
| `flow:*` | `flow:step:started`, `flow:step:completed` |
| `domain:*` | `domain:installed`, `domain:learning:completed` |
| `brain:*` | `brain:gate:created`, `brain:gate:approved` |
| `memory:*` | `memory:company:policy:updated` |

### 7.3 Pub/Sub API

```python
class EventBus:
    """Central Event Bus — Pub/Sub pattern"""
    
    def publish(self, event: Event):
        """Publish an event — all subscribers notified"""
    
    def subscribe(self, event_type: str, handler: Callable):
        """Register a handler for a specific event type"""
    
    def subscribe_pattern(self, pattern: str, handler: Callable):
        """Register handler with wildcard: 'runtime:*:completed'"""
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """Remove a handler"""
```

### 7.4 Event Store

All events are stored in an **Event Store** (StorageEngine-backed):

| Service | Storage | Duration |
|---------|---------|----------|
| **Current Workflow Events** | In-memory + StorageEngine | Until workflow ends |
| **Historical Events** | StorageEngine (compressed) | 30 days |
| **Archived Events** | Compressed JSON files | 1 year |
| **Audit Events** | StorageEngine (immutable) | Forever |

### 7.5 Current Brain EventStream vs Future Event Bus

| Feature | EventStream (Current) | Event Bus (Target) |
|---------|----------------------|-------------------|
| **scope** | Brain only | Entire system |
| **persistence** | StorageEngine | StorageEngine + tiered storage |
| **pub/sub** | ❌ emit only | ✅ subscribe + pattern |
| **correlation** | ❌ | ✅ correlation_id |
| **schema** | Free-form | Standard |
| **performance** | Single deque | Prioritized queue |

---

## 8. Tool Bus

### 8.1 Current Problem

Currently:
- Each agent calls `subprocess.run(["hermes", "chat", ...])` directly
- Tools are listed in `agent.tools` but the runtime doesn't guarantee availability
- No standard schema for tool definitions
- Limited tool sharing between agents

### 8.2 Tool Bus Architecture

The Tool Bus is an **abstraction layer** between Agents and tools:

```
Agent
  │
  │  Tool Call: {"tool": "web-search", "args": {"query": "..."}}
  ▼
┌─────────────────────────────────────────┐
│           Tool Bus                       │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────┐  │
│  │ Registry │  │ Validator│  │ Cache │  │
│  └──────────┘  └──────────┘  └──────┘  │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │         Rate Limiter                ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │         Security Layer              ││
│  └─────────────────────────────────────┘│
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐ ┌────────┐ ┌────────────┐
│ Built-in│ │ Domain │ │ 3rd Party │
│ Tools  │ │ Tools  │ │ Tools     │
└────────┘ └────────┘ └────────────┘
```

### 8.3 Tool Schema

```json
{
  "tool_id": "web-search",
  "name": "Web Search",
  "description": "Search the internet for information",
  "version": "1.0.0",
  "source": "built-in",
  "auth_required": false,
  
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query",
        "required": true
      },
      "limit": {
        "type": "integer",
        "description": "Number of results",
        "default": 5,
        "minimum": 1,
        "maximum": 50
      }
    }
  },
  
  "output_schema": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "url": {"type": "string"},
        "description": {"type": "string"}
      }
    }
  },
  
  "rate_limit": {
    "max_per_minute": 30,
    "max_per_hour": 500
  },
  
  "cost": {
    "per_call": 0.001,
    "currency": "USD"
  },
  
  "timeout": 15
}
```

### 8.4 Built-in Tools

| Tool | Description | Status |
|------|-------------|--------|
| `web-search` | Search the web | ✅ Existing |
| `web-extract` | Extract page content | ✅ Existing |
| `read-file` | Read files | ✅ Existing |
| `write-file` | Write files | ✅ Existing |
| `execute-python` | Run Python code | ✅ Existing |
| `database-query` | SQLite queries | ✅ Existing |
| `memory-read` | Read from memory | 🔧 Planned |
| `memory-write` | Write to memory | 🔧 Planned |
| `notify` | Send notifications (TG, Slack, ...) | ✅ Existing |
| `schedule` | Schedule tasks | ❌ Needs work |

Domain-specific tools (e.g., for Accounting):

| Tool | Description | Status |
|------|-------------|--------|
| `financial-statement-reader` | Extract data from PDF financials | ✅ Existing |
| `ratio-analyzer` | Calculate financial ratios | ✅ Existing |
| `tax-calculator` | Tax calculation per Iranian law | ❌ Needs data |
| `payslip-generator` | Generate payslip | ❌ Needs data |

### 8.5 Tool Bus Implementation Path

| Step | Work | Estimate |
|------|------|----------|
| 1 | Define Tool Schema | 1 day |
| 2 | Tool Registry (discovery + registration) | 1 day |
| 3 | Tool Validator | 1 day |
| 4 | Rate Limiter | 1 day |
| 5 | Security Layer | 2 days |
| 6 | Cache Layer | 1 day |
| 7 | Adapt existing tools to new Schema | 2 days |
| 8 | Tests | 2 days |
| **Total** | | **11 days** |

---

## 9. Domain SDK

### 9.1 Purpose

The Domain SDK is a set of tools, classes, and CLI commands that allow a developer to **build a new Domain for HiveOS** without deep kernel knowledge.

### 9.2 SDK Components

```
domain-sdk/
├── templates/              # Ready templates
│   ├── basic-domain/
│   ├── knowledge-domain/   # Knowledge-heavy (like Accounting)
│   └── service-domain/     # Service-oriented (like Notification)
├── cli/
│   ├── hive domain init    # Create new domain
│   ├── hive domain build   # Validate and build
│   ├── hive domain test    # Test domain
│   └── hive domain publish # Publish domain
├── core/
│   ├── BaseDomain.py       # Base Domain class
│   ├── BaseAgent.py        # Base Agent class
│   ├── BaseTool.py         # Base Tool class
│   └── BaseFlow.py         # Base Flow class
└── validators/
    ├── validate_manifest.py
    └── validate_schema.py
```

### 9.3 SDK Usage Example

```bash
# 1. Create new domain
hive domain init accounting

# 2. Define an agent
hive domain add-agent accounting financial-analyst

# 3. Define a flow
hive domain add-flow accounting financial-report

# 4. Validate
hive domain build accounting

# 5. Test
hive domain test accounting

# 6. Install in HiveOS
hive domain install accounting

# 7. Publish (to public registry)
hive domain publish accounting
```

### 9.4 Package Format

Domains are distributed as `.tar.gz` or a standalone repository:

```yaml
# domain.yaml — Domain manifest
domain:
  name: accounting
  version: 1.0.0
  label:
    en: "Iranian Accounting"
    fa: "حسابداری ایران"
  description:
    en: "Specialized domain for Iranian accounting"
    fa: "دامنه تخصصی حسابداری ایران"
  
  author: HiveOS Team
  license: MIT
  
  engine_requirement: ">= 0.12.0"
  
  dependencies:
    - general >= 1.0.0
  
  capabilities:
    - financial-statement-analysis
    - tax-calculation
    - payroll-processing
    - audit-support
  
  entry_points:
    agents: agents/blueprints/
    flows: flows/
    knowledge: knowledge/
    tools: tools/
```

### 9.5 SDK Classes

```python
from hiveos.sdk import BaseDomain, BaseAgent, BaseTool

class AccountingDomain(BaseDomain):
    """Accounting domain — registered in Domain Registry"""
    
    name = "accounting"
    version = "1.0.0"
    dependencies = ["general"]


class FinancialAnalyst(BaseAgent):
    """An agent for financial statement analysis"""
    
    name = "financial-analyst"
    domain = "accounting"
    tools = ["financial-statement-reader", "ratio-analyzer"]
    
    async def run(self, task: str, context: dict) -> dict:
        statements = await self.call_tool("financial-statement-reader", {
            "path": context["financial_statement_path"]
        })
        ratios = await self.call_tool("ratio-analyzer", {
            "data": statements
        })
        return {"ratios": ratios, "analysis": self._interpret(ratios)}


class FinancialStatementReader(BaseTool):
    """Tool for reading financial statements from PDF"""
    
    name = "financial-statement-reader"
    description = "Extract financial data from PDF statements"
    
    parameters = {
        "path": {"type": "string", "required": True}
    }
    
    async def run(self, path: str) -> dict:
        # Extraction logic
        return {"balance_sheet": ..., "income_statement": ...}
```

---

## 10. Plugin API

### 10.1 Philosophy

The Plugin API allows third-party developers to extend HiveOS without modifying the kernel. Key difference from Domain SDK:

| Domain SDK | Plugin API |
|-----------|------------|
| For building new Domains | For extending any system part |
| Fixed contracts (manifest, agents, flows) | Free-form — any extension type |
| Install via Domain Registry | Install via Plugin Manager |

### 10.2 Plugin Types

| Type | Description | Example |
|------|-------------|---------|
| **Tool Plugin** | Adds new tools | `stock-market-api` |
| **UI Plugin** | Adds dashboard pages | `custom-chart` |
| **Trigger Plugin** | New trigger type | `slack-command` |
| **Auth Plugin** | New auth method | `saml-sso` |
| **Storage Plugin** | New storage backend | `postgres-storage` |
| **Notification Plugin** | New notification channel | `whatsapp-notify` |

### 10.3 Plugin Lifecycle

```
Discovery → Registration → Activation → Runtime → Deactivation → Removal
```

### 10.4 Plugin Manifest

```yaml
# plugin.yaml
plugin:
  name: stock-market-api
  version: 1.0.0
  type: tool
  
  author: Third Party Dev
  
  engine_requirement: ">= 0.14.0"
  
  hooks:
    register_tools:
      - id: stock-price
        handler: tools/stock_price.py
  
  config:
    api_key_env: STOCK_API_KEY
    rate_limit: 100
```

### 10.5 Hooks

Each Plugin can "hook" into specific system points:

```python
class StockMarketPlugin(Plugin):
    """Stock market plugin — stock price search tool"""
    
    hooks = {
        # After plugin registration
        "on_activate": "self._setup_api",
        
        # Before any tool call from this plugin
        "before_tool_call": "self._check_rate_limit",
        
        # After any tool completes
        "after_tool_call": "self._log_usage",
        
        # On system shutdown
        "on_deactivate": "self._cleanup",
        
        # Add new endpoint to Dashboard API
        "register_api_routes": "self._add_routes",
    }
```

---

## 11. Bridge to Future Versions

This section shows which architectural layers each future version uses and what deliverables it produces.

### 11.1 Version Map

```
Version   Layers           Main Deliverable
───────   ──────────────   ───────────────────────────────
v0.12     Architecture     20-page Architecture Doc

v0.13     Planner          3 planning levels · Plan
                           Validator · API · Desktop UI

v0.14     Runtime          State Machine · Phase Executor
                           · Pause/Resume · HITL
                           · Schedule · Error Strategies

v0.15     Reflection       6 Reflection modules
                           · Success/Fail Analyzer
                           · Mistake Pattern Detection
                           · Improvement Suggestion
                           · Learning Persistence
                           · Cross-agent Knowledge Transfer
                           · Performance Trend Analysis

v0.16     Company Memory   6 company memory categories
                           · Company Memory Service
                           · Policy Engine
                           · Decision Logger
                           · Preference Store
                           · Planner + Runtime integration

v0.17     Knowledge Graph  3 graph layers
                           · Entity Extraction
                           · Relationship Mapping
                           · Query Engine
                           · Visualization
                           · Cross-Domain Linking

v1.0      Integration      First stable public release
```

### 11.2 Dependencies Between Layers

```
           v0.12 (Architecture Doc)
             │
             ▼
┌────────────────────────┐
│       v0.13            │
│      Planner           │
└──────────┬─────────────┘
           │ Produces Plan
           ▼
┌────────────────────────┐
│       v0.14            │
│      Runtime           │◄── Executes Plan
└──────────┬─────────────┘
           │ Produces Execution results
           ▼
┌────────────────────────┐
│       v0.15            │
│     Reflection         │◄── Learns from Execution
└──────────┬─────────────┘
           │ Stores learnings
           ▼
┌────────────────────────┐
│       v0.16            │
│   Company Memory       │◄── Holds organizational memory
└──────────┬─────────────┘
           │ Structures memory
           ▼
┌────────────────────────┐
│       v0.17            │
│   Knowledge Graph      │◄── Connects everything
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│        v1.0            │
│    Integration         │
└────────────────────────┘
```

### 11.3 What NOT to Build

Until v1.0, these are **excluded**:

| Item | Reason |
|------|--------|
| **CRM** | Core not stable — CRM is a Domain, not a layer |
| **HR Module** | HR domain added later as a Domain |
| **ERP Integration** | Unified ERP API after v1.0 |
| **Mobile App** | Focus on desktop + PWA |
| **Public Domain Registry** | Domain SDK must stabilize first |
| **Multi-language** | Persian + English only for v1.0 |
| **Real-time Collaboration** | Post v1.0 |

---

## 12. Architecture Decision Records

### ADR-001: Planner Before Runtime

**Status:** ✅ Accepted
**Context:** ChatGPT suggested building Runtime before Planner. The architecture team decided Planner first.
**Rationale:** Runtime must execute a Plan. Building Runtime without Planner yields the same simple execution engine — just with better state management.
**Consequence:** Timeline: v0.13 = Planner, v0.14 = Runtime.

### ADR-002: Event Bus Replaces Brain EventStream

**Status:** ✅ Accepted
**Context:** Brain EventStream currently handles only Brain events. A central Event Bus for the entire system is needed.
**Solution:** The Event Bus will extend the current EventStream — with pub/sub, correlation, and standard schema.
**Consequence:** Current EventStream is gradually replaced. No full rewrite needed — Event Bus can be a wrapper.

### ADR-003: Memory Model — 5 Levels

**Status:** ✅ Accepted
**Context:** Need multi-level memory structure to separate different scopes.
**Solution:** 5 levels: Session → Agent → Domain → Company → Long-term.
**Consequence:** Company Memory and Long-Term Memory implemented in v0.16 and v0.17.

### ADR-004: Tool Bus with Registry + Rate Limiter + Security

**Status:** ✅ Accepted
**Context:** Current tools lack standard schema and access control.
**Solution:** Tool Bus as middleware with Registry, Validator, Rate Limiter, and Security Layer.
**Consequence:** All existing tools must migrate to new Schema (backward-compatible change).

### ADR-005: Domain SDK Separates from Plugin API

**Status:** ✅ Accepted
**Context:** Domain SDK and Plugin API both help extend the system but have different scope.
**Solution:** Two separate APIs — Domain SDK for building new Domains with fixed contracts, Plugin API for extending any system part.
**Consequence:** Domain SDK designed in v0.12, implemented after Runtime stabilizes.

### ADR-006: Kernel Minimalism

**Status:** ✅ Accepted
**Context:** Tempting to give the kernel more responsibilities (Planning, Scheduling).
**Solution:** Kernel only has StorageEngine + Service Registry + Config + Logging + Lifecycle. Everything else is a separate service.
**Consequence:** Thin kernel — each layer independently testable and replaceable.

### ADR-007: StorageEngine Remains SQLite

**Status:** ✅ Accepted (for v1.0)
**Context:** Storage backend choice.
**Solution:** SQLite via current StorageEngine is sufficient for v1.0. Plugin API allows adding PostgreSQL, Redis later.
**Consequence:** Need stronger migration system — current MigrationRunner is adequate for now.

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **Agent** | An AI entity that performs a task |
| **Blueprint** | Definition of an Agent's type and capabilities |
| **Company Memory** | Shared memory across all Agents for policies and decisions |
| **DAG** | Directed Acyclic Graph — dependency model |
| **Domain** | A specialized knowledge area (e.g., accounting, tax) |
| **Domain SDK** | Tools for building new Domains |
| **Event Bus** | Central Pub/Sub system for component communication |
| **Execution Plan** | Planner output — a complete DAG of agents and dependencies |
| **Flow** | A multi-step workflow |
| **HITL** | Human in the Loop — human approval points |
| **Kernel** | Minimal set of fundamental services |
| **Knowledge Graph** | Relationships between organizational entities |
| **Planner** | Component that converts a Goal into a Plan |
| **Plugin** | Third-party extension |
| **Reflection** | Learning from past executions |
| **Runtime** | Component that executes and manages the Plan |
| **StorageEngine** | SQLite-based persistence layer |
| **Tool** | A capability usable by an Agent |
| **Tool Bus** | Tool management and security layer |
| **Workflow** | A complete execution of a Goal |

---

## Appendix B: Current File Map

```
src/hiveos/
├── __init__.py
├── cli.py                  # CLI main entry
├── dsl.py                  # Flow DSL parser
├── engine.py               # Flow Engine (current)
├──
├── brain/                  # Brain — Event Stream, Decision Tracer, Approval Gate
│   ├── event_stream.py
│   ├── decision_tracer.py
│   └── approval_gate.py
├── cli/                    # CLI commands
│   ├── main.py
│   ├── run.py
│   └── build.py
├── dashboard/              # FastAPI Dashboard
│   └── server.py
├── desktop/                # pywebview Desktop Shell
│   └── app.py
├── domain/                 # Domain Registry
│   ├── manager.py
│   └── registry.py
├── learning/               # Learning — Logger + Analytics
│   ├── logger.py
│   └── analytics.py
├── license/                # Licensing
├── mothership/             # Mothership — Agent Registry, Task Router, Comms
│   ├── agent_registry.py
│   ├── task_router.py
│   ├── communication_bus.py
│   ├── resilience.py
│   └── server.py
├── playground/             # Playground — Canvas, Component Engine
│   ├── playground.py
│   ├── component_engine.py
│   ├── runner.py
│   └── library.py
├── registry/               # Package Registry
├── storage/                # StorageEngine
│   ├── engine.py
│   └── migrations.py
├── sync/                   # Knowledge Sync
├── update/                 # Auto-updater
├── utils/                  # Utilities
│   ├── config.py
│   ├── knowledge.py
│   └── validator.py
└── workspace/              # Multi-tenant Workspaces
```

---

> **Author:** HiveOS Architecture Team — July 2026
> 
> **Version:** v0.12 (Architecture Draft)
> 
> **Related Files:**
> - `docs/02-Architecture/01-high-level-arch.md` — Previous architecture overview
> - `docs/02-Architecture/03-domain-plugin-system.md` — Domain Plugin architecture
> - `docs/02-Architecture/04-architecture-v1.0.fa.md` — Persian version of this document
