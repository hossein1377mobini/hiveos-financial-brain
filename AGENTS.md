# HiveOS — Agent Boot File 🐝

> Auto-loaded by Hermes when working in hive-os.
> Contains COMPLETE project state for cross-session continuity.

---

## 📌 Current Phase

| Phase | Status | Version |
|-------|--------|---------|
| Phase 0 (Foundation) | ✅ | v0.1.0 |
| Phase 1 (Playground CLI) | ✅ | v0.2.0 |
| Phase 2 (Integration) | ✅ | v0.3.0 |
| Phase 3 (Packaging) | ✅ | v0.4.0 |
| Phase 4 (Mothership) | ✅ | v0.4.0 |
| Phase 5 (Enterprise) | ✅ | v0.6.0 |
| Phase D1 (Accounting) | 🏗️ 70% | v0.6.0 |
| Phase 6 (Playground UI) | ⏳ | — |
| Phase 7 (Brain) | ⏳ | — |
| Phase 8 (Learning) | ⏳ | — |

---

## 🎯 Project Vision (v2.0)

HiveOS is a **Multi-Agent Operating System** with 5 pillars:

1. **Engine** — Core OS (Flow DSL, Engine, Mothership, Enterprise features) ✅
2. **Domains** — Pluggable knowledge domains (Accounting D1 🏗️)
3. **Playground** — Visual interactive flow builder ⏳
4. **Brain** — 3D neural glass-box visualization ⏳
5. **Learning** — Self-improving system ⏳

**Guiding Principles:**
- **Glass Box** — Every action visible, traceable, explainable
- **Human-in-the-Loop** — Critical decisions need human approval
- **Domain-Native** — Domains are first-class plugins
- **Self-Learning** — Every execution makes the system smarter

---

## 🔧 Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                         🧠 BRAIN                            │
│              3D Neural Visualization — Glass Box            │
├──────────────────────────────────────────────────────────────┤
│                         🎮 PLAYGROUND                       │
│          Visual Flow Builder — Drag, Drop, Configure        │
├──────────────────────────────────────────────────────────────┤
│                         🔧 ENGINE                           │
│  CLI • Flow Engine • Mothership • RBAC • Audit • Workspace  │
│  License • Dashboard • Registry • Package • Communication   │
├──────────────────────────────────────────────────────────────┤
│                         🧩 DOMAINS                          │
│     Accounting (D1) • Medical • Legal • Engineering ...     │
└──────────────────────────────────────────────────────────────┘
```

---

## ✅ What's Built (v0.6.0 — 273 tests)

### Core Infrastructure
| Component | Test Count | Status |
|-----------|-----------|--------|
| Flow Engine | 13 | ✅ |
| Agent Registry | 20 | ✅ |
| Task Router | 16 | ✅ |
| Communication Bus | 14 | ✅ |
| Resilience Engine | 20 | ✅ |
| Sync (Node Registry) | 12 | ✅ |
| Package Registry | 16 | ✅ |
| RBAC | 36 | ✅ |
| Audit Trail | 20 | ✅ |
| Dashboard | 23 | ✅ |
| Workspace (Multi-tenant) | 38 | ✅ |
| License (Pricing) | 32 | ✅ |

### CLI Commands
```
hive
 ├── flow run/validate/list/state/clear-state
 ├── package build/install/list/publish
 ├── registry list/search/info/remove/verify
 ├── mothership agent/route/bus/health/server
 ├── rbac user/role
 ├── audit list/search/stats/search-gbrain/sync-gbrain/rotate
 ├── dashboard start/stop/status
 ├── workspace create/list/info/update/remove/activate member
 ├── license info/activate/deactivate/upgrade/tiers/check
 └── util init/info
```

### Domain System (Accounting — D1)
```
domains/accounting/
├── domain.yaml                     ★ Domain manifest
├── knowledge/
│   ├── tree.yaml                   ★ 200+ node knowledge tree (A-J)
│   └── references/                 Official Iranian curricula
├── agents/
│   └── blueprints/                 ★ 29 agent blueprint YAMLs
│       ├── 6 orchestrators         (master-financial-assistant, etc.)
│       └── 23 specialists          (financial-recorder, auditor, etc.)
└── flows/                          ★ 6 flow template YAMLs
    ├── financial-close.yaml        بستن حساب
    ├── tax-return.yaml             اظهارنامه مالیاتی
    ├── audit-engagement.yaml       حسابرسی
    ├── company-valuation.yaml      ارزش‌گذاری
    ├── annual-budget.yaml          بودجه
    └── fraud-investigation.yaml    تقلب
```

---

## 🏗️ Next: Phase 6 — Playground

### What to Build First

**Step 1: Core APIs** (session 1)
- `POST /api/playground/validate` — Validate flow YAML
- `POST /api/playground/auto-agents` — Task → auto agent team (domain.yaml + blueprints)
- `GET /api/templates/` — List domain flow templates

**Step 2: Visual Canvas** (session 2)
- Integrate React Flow library into dashboard
- Drag & drop agent nodes, gates, conditions
- Edge drawing for dependencies
- Node configuration panels

**Step 3: Run & Debug** (session 3)
- `POST /api/playground/run` — Execute flow
- `WS /api/playground/run/{id}/stream` — Live logs + status
- Run progress visualization
- Approval gate interaction

**Step 4: Polish** (session 4)
- Template customizer
- User flow library
- Visual conditions builder
- Subflow support

### Flow Components to Implement
- [ ] Trigger (manual, cron, webhook)
- [ ] Task (agent node)
- [ ] Condition (if/else)
- [ ] Switch (multi-branch)
- [ ] Loop (repeat)
- [ ] Parallel (concurrent)
- [ ] Join (sync)
- [ ] Approval Gate (human-in-loop)
- [ ] Timer (delay)
- [ ] Error Handler (retry/skip/abort)
- [ ] Transform (data mapping)

---

## 🧠 Next: Phase 7 — Brain

### What to Build

**Core Engine (server-side):**
- Event Stream pipeline (agent lifecycle → events)
- Decision Tracer (trace every decision path)
- Approval Gate Engine (create → notify → approve/reject → log)
- Brain API: `WS /api/brain/stream`, `GET /api/brain/state`, `GET /api/brain/decision/{id}`

**3D Visualization (client-side):**
- Three.js/WebGL neural network renderer
- Agents as glowing spheres with status colors
- Data flow particles between agents
- Click → inspect agent details
- Decision path overlay on neural view
- Approval gate UI (pending gates list, approve/reject actions)

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `docs/01-Vision/01-product-vision.md` | Full product vision v2.0 (5 pillars) |
| `docs/01-Vision/03-playground-vision.md` | Playground detailed spec |
| `docs/01-Vision/04-brain-vision.md` | Brain + Glass Box detailed spec |
| `docs/01-Vision/02-domain-ecosystem-vision.md` | Multi-domain ecosystem |
| `docs/02-Architecture/01-high-level-arch.md` | Architecture docs |
| `docs/02-Architecture/03-domain-plugin-system.md` | Domain plugin architecture |
| `ROADMAP.md` | Roadmap with Phases 6/7/8 |
| `MANIFEST.md` | Product manifesto |
| `AGENTS.md` | This file — full project context |
| `hiveos-skill.md` | Hermes skill definition (needs update) |

---

## 🔧 Common Commands

```bash
cd "C:\Users\Hossein Mobini\Desktop\hive-os"
source .venv/Scripts/activate
uv pip install -e .                    # after code changes
# CLI
hive --version
hive license activate hive-pro-demo
hive flow validate prototype/
hive flow run prototype/hello-flow/hello.yml
# Tests
python -m pytest tests/ -v
python -m pytest tests/test_license.py -v
# Git
git add -A && git commit -m "..." && git push origin main
```

---

## 📋 Session History

| Date | Version | What Was Done |
|------|---------|---------------|
| 2026-07-13 | v0.1–0.5 | Foundation, Playground CLI, Integration, Packaging, Mothership |
| 2026-07-14 | v0.5.0 | RBAC — 36 tests |
| 2026-07-14 | v0.5.1 | Audit Trail — 20 tests |
| 2026-07-14 | v0.5.2 | Dashboard — FastAPI + SPA — 23 tests |
| 2026-07-14 | v0.5.3 | Multi-tenant Workspaces — 38 tests |
| 2026-07-14 | v0.6.0 | License pricing + 29 agent blueprints + 6 flow templates + bilingual README |
| **Next** | **v0.7.0** | **Phase 6: Playground Core APIs** |

---

## 🎯 Full Task Backlog (for next session)

### Phase 6: Playground — Part 1 (Core APIs)
- [ ] **P6.1** — `POST /api/playground/validate` endpoint in dashboard server
- [ ] **P6.2** — Auto-agent generation API (parse task → match domain agents)
- [ ] **P6.3** — Template browser API (list domain flow templates)
- [ ] **P6.4** — Integrate React Flow into dashboard HTML
- [ ] **P6.5** — Canvas: drag-drop agents, draw edges, node config panels
- [ ] **P6.6** — `POST /api/playground/run` — execute flow from dashboard
- [ ] **P6.7** — WebSocket streaming of execution progress + logs
- [ ] **P6.8** — Approval gate UI + engine
- [ ] **Tests** — Playground module tests
- [ ] **Docs** — Update ROADMAP, AGENTS

### Phase D1: Remaining
- [ ] Hermes skills for accounting agents
- [ ] `hive domain` CLI
