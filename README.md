# HiveOS 🐝 — Multi-Agent Operating System

**Version 0.10.0** | [فارسی](README.fa.md)

**Orchestrate teams of AI agents. Package workflows. Ship them anywhere.**

HiveOS is a platform for designing, deploying, and orchestrating Multi-Agent Systems (MAS). It transforms a collection of AI agents into a structured, coordinated team — each with its own skills, knowledge, and role in a defined workflow.

---

## ✨ Why HiveOS?

Most agent frameworks stop at "one agent per task." HiveOS treats agents as **first-class OS processes**:

| Concept | What it means |
|---------|---------------|
| 🧠 **Flow Engine** | Declarative YAML DSL to define agent teams, dependencies, triggers |
| 🌍 **Mothership** | Central orchestrator with satellite node execution |
| 📦 **Packaging** | Tar.gz format to bundle and ship agent ecosystems |
| 🔐 **RBAC** | Role-based access control with built-in roles |
| 📜 **Audit Trail** | JSONL daily logs + gbrain semantic search |
| 📊 **Dashboard** | Dark-themed SPA to monitor agents, flows, and nodes |
| 🏢 **Multi-tenant** | Isolated workspaces per team/org |
| 💰 **Pricing** | 4-tier license system with feature gating |
| 🧩 **Domain Plugins** | Knowledge domains as installable plugins |

---

## 🏗️ Architecture

```
User → Flow DSL YAML → Flow Engine (topological sort)
                         ├── Agent 1 (skills: A, B) ──┐
                         ├── Agent 2 (depends: 1) ───┤→ Hermes subagent
                         ├── Agent 3 (depends: 1) ───┘
                         └── Agent 4 (depends: 2, 3) → Final output
```

```
┌──────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │Accounting│  │ Medical  │  │ Legal    │   ...          │
│  │ Domain   │  │ Domain   │  │ Domain   │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
├───────┴──────────────┴──────────────┴─────────────────────┤
│                     HIVEOS CORE                          │
│  ┌────────┐  ┌──────────┐  ┌────────┐  ┌──────────────┐ │
│  │  Flow  │  │  Agent   │  │ Package│  │ Communication│ │
│  │ Engine │  │ Registry │  │ Manager│  │     Bus      │ │
│  └────────┘  └──────────┘  └────────┘  └──────────────┘ │
│  ┌────────┐  ┌──────────┐  ┌────────┐  ┌──────────────┐ │
│  │  RBAC  │  │  Audit   │  │  CLI   │  │  Dashboard   │ │
│  │        │  │  Trail   │  │  Shell │  │     UI       │ │
│  └────────┘  └──────────┘  └────────┘  └──────────────┘ │
│  ┌────────┐  ┌──────────┐  ┌────────┐                   │
│  │License │  │Workspace │  │Domain  │                   │
│  │Manager │  │ Manager  │  │ Plugins│                   │
│  └────────┘  └──────────┘  └────────┘                   │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   Hermes      │
                 │   Agent       │
                 │   Runtime     │
                 └───────────────┘
```

---

## 🚀 Quick Start

```bash
# Install
cd hive-os
uv venv && source .venv/Scripts/activate       # Windows
uv pip install .

# See the CLI
hive --version

# Run a sample flow
hive flow run prototype/hello-flow/hello.yml

# Validate flows in a directory
hive flow validate prototype/

# Run all tests
python -m pytest tests/ -v
```

---

## 🖥️ CLI Reference

```
hive
 ├── flow run/validate/list/state/clear-state
 ├── package build/install/list/publish
 ├── registry list/search/info/remove/verify
 ├── mothership
 │    ├── agent register/list/info/remove/capabilities/heartbeat
 │    ├── route assign/reroute/metrics/rules
 │    ├── bus publish/subscribe/stats
 │    ├── health check/monitor/status/failures/circuits/reassignments
 │    └── server start/stop/status
 ├── rbac
 │    ├── user add/list/remove/set-role/set-api-key/enable/disable
 │    └── role add/list/show/remove
 ├── audit list/search/stats/search-gbrain/sync-gbrain/rotate
 ├── dashboard start/stop/status
 ├── workspace create/list/info/update/remove/activate member
 ├── license info/activate/deactivate/upgrade/tiers/check
 └── util init/info
```

### License Commands

```bash
hive license info              # Show current license
hive license activate <key>    # Activate demo or real key
hive license deactivate        # Revert to Free tier
hive license upgrade pro       # Upgrade/downgrade tier
hive license tiers             # Compare all tiers
hive license check <feature>   # Feature availability check
```

**Demo keys:** `hive-pro-demo`, `hive-ent-demo`, `hive-ult-demo`

---

## 🧩 Domain Plugin System

HiveOS is **domain-agnostic** — any knowledge domain can be installed as a plugin.

### 🔢 Accounting Domain (D1)

The first domain: a complete accounting & finance assistant built from official Iranian higher education curricula.

```
domains/accounting/
├── domain.yaml                     # Domain manifest (29 agents, 6 flows)
├── knowledge/
│   ├── tree.yaml                   # ★ 200+ node knowledge tree (10 branches A-J)
│   └── references/                 # Source curricula
├── agents/
│   └── blueprints/                 # ★ 29 agent blueprint YAML files
│       ├── master-financial-assistant.yaml     # Level 3 orchestrator
│       ├── financial-orchestrator.yaml         # Level 2 orchestrators
│       ├── management-orchestrator.yaml
│       ├── audit-orchestrator.yaml
│       ├── tax-orchestrator.yaml
│       ├── advisory-orchestrator.yaml
│       ├── financial-recorder.yaml             # Level 1 specialists
│       ├── financial-reporter.yaml
│       ├── ...                                 # 23 more specialists
└── flows/                         # ★ 6 flow template YAML files
    ├── financial-close.yaml       # Period-end closing workflow
    ├── tax-return.yaml            # Tax return preparation
    ├── audit-engagement.yaml      # Audit engagement workflow
    ├── company-valuation.yaml     # Company valuation
    ├── annual-budget.yaml         # Annual budget preparation
    └── fraud-investigation.yaml   # Fraud investigation
```

---

## 📋 Roadmap

### ✅ Phase 0: Foundation
Flow DSL, Flow Engine, CLI, package system, prototype flows

### ✅ Phase 1: Playground
Flow DSL v0.1, state persistence, error handling, 3-agent demo

### ✅ Phase 2: Integration
Hermes subagent spawning, resume support, retry/cascade-skip, knowledge sync

### ✅ Phase 3: Packaging
Tar.gz packages, local registry, remote registry client, CLI commands

### ✅ Phase 4: Mothership
Agent registry with capabilities, task routing (5 strategies), communication bus (pub/sub), resilience engine, FastAPI HTTP server

### ✅ Phase 5: Enterprise
RBAC (36 tests), Audit Trail (20 tests), Dashboard (23 tests), Multi-tenant workspaces (38 tests), Pricing/license tiers (32 tests)

### 🏗️ Phase D1: Accounting Domain 🏗️
- ✅ Knowledge tree (200+ nodes, 10 branches)
- ✅ Domain manifest (29 agents, 6 flows)
- ✅ Domain architecture docs
- ✅ 29 agent blueprints (YAML)
- ✅ 6 flow templates (YAML)
- ⏳ Hermes skills for each agent
- ⏳ Agent auto-generation API
- ⏳ Template browser API

### ⏳ Phase D2: Domain Plugin System
- `hive domain` CLI, registry, mothership loading

---

## 🎯 Upcoming: Phase 6 — Playground (Interactive UI)

**Goal:** Replace YAML-only flows with a visual drag-and-drop flow builder.

| Priority | Feature |
|----------|---------|
| 🔴 | Flow Validator API + Auto-Agent API |
| 🔴 | Template Browser (preview domain flows) |
| 🔴 | Visual Canvas (React Flow, drag & drop) |
| 🔴 | Run/Debug with live streaming logs |
| 🟡 | Approval Gates (human-in-the-loop) |
| 🟡 | Template Customizer + Flow Library |
| 🟢 | Visual Conditions + Subflows |

Flow components: Trigger, Task, Condition, Switch, Loop, Parallel, Join, Approval Gate, Timer, Error Handler, Transform, Subflow

---

## 🎯 Upcoming: Phase 7 — Brain (3D Glass Box)

**Goal:** Complete transparency with real-time 3D neural visualization.

| Priority | Feature |
|----------|---------|
| 🔴 | Event Stream — agent lifecycle pipeline |
| 🔴 | Decision Tracer — trace every path |
| 🔴 | Approval Gate Engine |
| 🟡 | 3D Neural View (Three.js/WebGL) |
| 🟡 | Real-time WebSocket streaming |
| 🟢 | Interactive exploration + Historical replay |

---

## 🎯 Upcoming: Phase 8 — Learning

- Execution Analytics
- Pattern Recognition → Template Suggestions
- Knowledge Accumulation
- Adaptive Routing

---

## 🧪 Test Stats

| Module | Tests | Status |
|--------|-------|--------|
| Flow Engine | 13 | ✅ |
| Agent Registry | 20 | ✅ |
| Task Router | 16 | ✅ |
| Communication Bus | 14 | ✅ |
| Resilience | 20 | ✅ |
| Sync (Node Registry) | 12 | ✅ |
| Package Registry | 16 | ✅ |
| RBAC | 36 | ✅ |
| Audit Trail | 20 | ✅ |
| Dashboard | 23 | ✅ |
| Workspace (Multi-tenant) | 38 | ✅ |
| License (Pricing) | 32 | ✅ |
| **Total** | **273** | **✅ All Passing** |

---

## 📁 Project Structure

```
hive-os/
├── src/hiveos/                  # Python package
│   ├── cli/main.py              # CLI entry point (all commands)
│   ├── dsl.py                   # Flow DSL definitions
│   ├── engine.py                # Flow execution engine
│   ├── license/                 # Pricing & feature gating
│   │   ├── models.py            # LicenseTier, FeatureFlag, License
│   │   └── manager.py           # LicenseManager (YAML persistence)
│   ├── rbac/                    # Role-based access control
│   ├── audit/                   # Audit trail (JSONL + gbrain)
│   ├── dashboard/               # Web UI (FastAPI + SPA)
│   ├── workspace/               # Multi-tenant workspaces
│   ├── mothership/              # Agent registry, task router, bus, resilience
│   ├── registry/                # Package registry (local + remote)
│   ├── sync/                    # Node registry, knowledge sync
│   ├── package/                 # Package builder/installer
│   └── utils/                   # Config, validator, knowledge manager
├── domains/                     # ★ Domain plugins
│   └── accounting/              # First domain: Accounting & Finance
│       ├── domain.yaml          # Domain manifest
│       ├── knowledge/tree.yaml  # Knowledge tree (200+ nodes)
│       ├── agents/blueprints/   # 29 agent blueprint YAML files
│       └── flows/               # 6 flow template YAML files
├── docs/                        # Knowledge base (Obsidian vault)
│   ├── 01-Vision/               # Product vision, domain ecosystem
│   ├── 02-Architecture/         # Architecture docs, ADRs
│   ├── 04-Meetings/             # Session logs
│   └── 06-Research/             # Domain research notes
├── prototype/                   # Example flows
├── tests/                       # 273 tests
├── ROADMAP.md                   # Live roadmap
├── MANIFEST.md                  # Product manifesto
└── AGENTS.md                    # Agent boot file (auto-loaded by Hermes)
```

---

## 📄 Documentation

| File | Purpose |
|------|---------|
| `README.md` | English overview (this file) |
| `README.fa.md` | Persian overview |
| `ROADMAP.md` | Live product roadmap |
| `MANIFEST.md` | Product manifesto & principles |
| `AGENTS.md` | Full project context (auto-loaded by Hermes) |
| `hiveos-skill.md` | Hermes skill definition |
| `docs/01-Vision/01-product-vision.md` | Product vision |
| `docs/01-Vision/02-domain-ecosystem-vision.md` | Domain ecosystem vision |
| `docs/01-Vision/02-accounting-direction.md` | Accounting domain direction |
| `docs/02-Architecture/01-high-level-arch.md` | High-level architecture |
| `docs/02-Architecture/02-flow-dsl.md` | Flow DSL specification |
| `docs/02-Architecture/03-domain-plugin-system.md` | Domain plugin system |
| `docs/02-Architecture/ADR/` | Architecture Decision Records |

---

## 🔧 Development

```bash
# Setup
cd hive-os
python -m venv .venv && source .venv/Scripts/activate
uv pip install -e .

# Run tests
python -m pytest tests/ -v

# Run a specific test module
python -m pytest tests/test_license.py -v

# Install package
uv pip install .

# Build distribution
python -m build
```

---

## 📜 License

**HiveOS Enterprise** — Proprietary

Tiered licensing: Free, Pro, Enterprise, Ultimate.
See `hive license` or `hive license tiers` for details.

---

## 🌐 Links

- **GitHub:** [hossein1377mobini/hiveos-financial-brain](https://github.com/hossein1377mobini/hiveos-financial-brain)
- **Author:** Hossein Mobini — PhD Researcher (CVC/Entrepreneurship)
