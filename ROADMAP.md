# HiveOS Roadmap 🗺️

> **Vision:** A Multi-Agent Operating System with a visual Playground, transparent Brain, self-learning capabilities, and pluggable domain knowledge.

---

## ✅ Done: Infrastructure (v0.1.0 — v0.6.0)

### Phase 0: Foundation ✅
| Task | Status | Notes |
|------|--------|-------|
| Product KB structure | ✅ | docs/ as Obsidian vault |
| Git init & version control | ✅ | GitHub: hossein1377mobini/hiveos-financial-brain |
| Hermes skill | ✅ | `hiveos-skill.md` — installable |
| Python package | ✅ | pyproject.toml, `uv pip install .` |
| Flow DSL + Validator | ✅ | YAML schema + structural validation |
| Flow Engine | ✅ | Topological sort, sequential agent execution |
| CLI (hive flow/package/util) | ✅ | 8 subcommands |
| Package builder/installer | ✅ | tar.gz format, manifest.yaml |

### Phase 1: Playground (CLI) ✅
- [x] Flow DSL v0.1
- [x] Flow Engine (Hermes delegate_task chain)
- [x] 3-agent demo flow
- [x] State persistence
- [x] Error handling (retry, cascade skip)

### Phase 2: Integration ✅
- [x] Hermes subagent spawning
- [x] State persistence with resume
- [x] Retry / cascade skip / status tracking
- [x] Knowledge sync (mothership → satellites)

### Phase 3: Packaging ✅
- [x] Package registry (YAML local catalog)
- [x] `hive package publish`
- [x] `hive registry` (list/search/info/remove/verify)
- [x] Remote registry client (HTTP)

### Phase 4: Mothership ✅
- [x] Agent Registry (capabilities, heartbeat)
- [x] Task Router (5 strategies)
- [x] Communication Bus (pub/sub, 2 backends)
- [x] Resilience (health checker, circuit breaker, reassignment)
- [x] Mothership Server (FastAPI REST API)
- [x] Mothership CLI (agent/route/bus/health/server)

### Phase 5: Enterprise ✅
- [x] RBAC (models, manager, server auth, CLI, 36 tests)
- [x] Audit Trail (JSONL + gbrain sync, 20 tests)
- [x] Dashboard (FastAPI + SPA, 23 tests)
- [x] Multi-tenant workspaces (38 tests)
- [x] Pricing model — license tiers (32 tests)

**Test total: 273** ✅

---

## 🏗️ In Progress: Domain System

### Phase D1: Accounting Domain 🏗️
- [x] Knowledge tree (200+ nodes, 10 branches A-J)
- [x] Domain manifest (29 agents, 6 flows)
- [x] Domain architecture docs
- [x] 29 agent blueprints (YAML)
- [x] 6 flow templates (YAML)
- [ ] Hermes skills per agent
- [ ] Agent auto-generation API
- [ ] Template browser API

### Phase D2: Domain Plugin CLI ⏳
- [ ] `hive domain` (list/info/install/remove/init)
- [ ] Domain registry (discover/shared)
- [ ] Mothership domain loading
- [ ] Cross-domain dependency resolution

### Phase D3: Next Domain ⏳
- [ ] Choose domain (medical, legal, engineering...)
- [ ] Build knowledge tree + agents + flows
- [ ] Publish to domain registry

---

## 🎯 Phase 6: Playground (Interactive Flow Builder) ⏳

**Goal:** Replace YAML-only flow creation with a visual, interactive flow builder in the Dashboard.

| Priority | Task | Description |
|----------|------|-------------|
| 🔴 P6.1 | **Flow Validator API** | REST endpoint to validate flow YAML with rich error messages |
| 🔴 P6.2 | **Auto-Agent API** | Task description → auto-select agents from domain |
| 🔴 P6.3 | **Template Browser** | Browse/preview domain flow templates |
| 🔴 P6.4 | **Visual Flow Canvas** | Drag & drop flow builder (React Flow) |
| 🔴 P6.5 | **Run/Debug with streaming** | Execute + streaming logs via WebSocket |
| 🟡 P6.6 | **Approval Gates UI** | Human-in-loop gates in dashboard |
| 🟡 P6.7 | **Template Customizer** | Clone + customize existing templates |
| 🟡 P6.8 | **Flow Library** | Save, version, share user-created flows |
| 🟢 P6.9 | **Visual Conditions** | Expression builder for branching |
| 🟢 P6.10 | **Subflows** | Nest flows within flows |

### Flow Components (from automation standards)

| Component | Description |
|-----------|-------------|
| **Trigger** | Manual, cron, webhook, event |
| **Task** | Agent action |
| **Condition** | If/else branch |
| **Switch** | Multi-branch routing |
| **Loop** | Repeat until condition |
| **Parallel** | Concurrent agent execution |
| **Join** | Sync parallel branches |
| **Approval Gate** | Human must approve/reject |
| **Timer** | Wait/delay |
| **Error Handler** | Retry, skip, abort, notify |
| **Subflow** | Nested flow |
| **Transform** | Map data between agents |

---

## 🎯 Phase 7: Brain (3D Neural Visualization) ⏳

**Goal:** Complete transparency with a real-time 3D neural visualization.

| Priority | Task | Description |
|----------|------|-------------|
| 🔴 P7.1 | **Event Stream** | Agent lifecycle events → streaming pipeline |
| 🔴 P7.2 | **Decision Tracer** | Trace every decision path start→finish |
| 🔴 P7.3 | **Approval Gate Engine** | Gate lifecycle: create→notify→approve/reject→log |
| 🟡 P7.4 | **Brain API** | REST + WebSocket endpoints for neural data |
| 🟡 P7.5 | **3D Neural View** | Three.js/WebGL brain visualization |
| 🟡 P7.6 | **Real-time Updates** | WebSocket streaming to neural view |
| 🟢 P7.7 | **Interactive Exploration** | Click agents, inspect details |
| 🟢 P7.8 | **Historical Replay** | Replay past executions in neural view |

---

## 🎯 Phase 8: Learning (Self-Improving System) ⏳

**Goal:** Every execution makes the system smarter.

| Priority | Task | Description |
|----------|------|-------------|
| 🟡 P8.1 | **Execution Analytics** | Track flow performance, bottlenecks, failures |
| 🟡 P8.2 | **Pattern Recognition** | Identify common patterns → suggest templates |
| 🟢 P8.3 | **Knowledge Accumulation** | Agents contribute back to domain knowledge |
| 🟢 P8.4 | **Adaptive Routing** | Smarter agent selection based on history |

---

## 📊 Legend

| Priority | Meaning |
|----------|---------|
| 🔴 High | Core functionality — must have for next release |
| 🟡 Medium | Important but can wait |
| 🟢 Low | Nice to have — when core is solid |

---

## 📈 Progress Summary

```
Phase 0-5 (Infrastructure):  ████████████████████████ 100%  (273 tests)
Phase D1 (Accounting):       ████████████████░░░░░░░░  70%
Phase D2 (Domain CLI):       ░░░░░░░░░░░░░░░░░░░░░░░░   0%
Phase 6 (Playground):        ░░░░░░░░░░░░░░░░░░░░░░░░   0%
Phase 7 (Brain):             ░░░░░░░░░░░░░░░░░░░░░░░░   0%
Phase 8 (Learning):          ░░░░░░░░░░░░░░░░░░░░░░░░   0%
```
