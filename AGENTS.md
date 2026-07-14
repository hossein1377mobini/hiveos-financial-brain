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
| Phase 6 (Playground) | ✅ Core APIs | v0.7.0 |
| Phase 7 (Brain) | ✅ Core Engine | v0.7.0 |
| Phase 8 (Learning) | ✅ Passive Logger | v0.7.0 |

---

## 🎯 Project Vision (v2.0)

HiveOS is a **Multi-Agent Operating System** with 5 pillars:

1. **Engine** — Core OS (Flow DSL, Engine, Mothership, Enterprise features) ✅
2. **Domains** — Pluggable knowledge domains (Accounting D1 🏗️)
3. **Playground** — Visual interactive flow builder ✅ Core APIs / ⏳ Canvas UI
4. **Brain** — 3D neural glass-box visualization ✅ Core Engine / ⏳ 3D Viz
5. **Learning** — Self-improving system ✅ Passive Logger / ⏳ Analytics

**Guiding Principles:**
- **Glass Box** — Every action visible, traceable, explainable
- **Human-in-the-Loop** — Critical decisions need human approval
- **Domain-Native** — Domains are first-class plugins
- **Self-Learning** — Every execution makes the system smarter

---

## ✅ What's Built (v0.7.0 — 329 tests)

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

### ✅ Phase 6: Playground — Part 1 (v0.7.0)
| Task | Status | Description |
|------|--------|-------------|
| **P-01** `POST /api/playground/validate` | ✅ | Flow YAML validation with rich errors/warnings |
| **P-02** `POST /api/playground/auto-agents` | ✅ | Task description → auto-select domain agents (keyword scoring) |
| **P-03** `GET /api/playground/templates` | ✅ | Browse domain flow templates with metadata |
| **P-04** Visual Canvas (React Flow) | ⏳ | Next session |
| **P-05** Run/Debug + WebSocket | ⏳ | Next session |

### ✅ Phase 7: Brain — Part 1 (v0.7.0)
| Task | Status | Description |
|------|--------|-------------|
| **B-01** Event Stream Pipeline | ✅ | Agent lifecycle events with filtering + stats |
| **B-02** Decision Tracer | ✅ | Trace every decision path + step tracking |
| **B-03** Approval Gate Engine | ✅ | Create/approve/reject/expire gates with stats |
| **B-04** Brain API (REST) | ✅ | All routes: /api/brain/events, /traces, /gates |
| **B-05** 3D Neural View | ⏳ | Next session |

### ✅ Phase 8: Learning — Part 1 (v0.7.0)
| Task | Status | Description |
|------|--------|-------------|
| **L-01** Execution Logger | ✅ | Passive in-memory collection + stats + trends |
| **L-02** Execution Analytics | ⏳ | Next session |

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

---

## 🎯 Next: Phase 6 — Playground Canvas UI

### What to Build Next

| Priority | Task | Layer | Status |
|----------|------|-------|--------|
| 🔴 | **P-04** Visual Canvas — HTML5 Canvas flow builder in dashboard | 🎮 Playground | ✅ Done |
| 🔴 | **P-05** `POST /api/playground/run` + `WS /api/playground/run/{id}/stream` | 🎮 Playground | ✅ Done |
| 🔴 | **P-06** Approval Gates UI in dashboard | 🎮 Playground | ✅ Done |
| 🔴 | **B-05** 3D Neural View — Three.js/WebGL in dashboard | 🧠 Brain | ✅ Done |
| 🟡 | **P-07** Template Customizer | 🎮 Playground | ⏳ |
| 🟡 | **P-08** Flow Library (save/share user flows) | 🎮 Playground | ⏳ |
| 🟡 | **L-02** Execution Analytics + Pattern Recognition | 📈 Learning | ✅ Done |
| 🟢 | **D-04** Hermes skills for accounting agents | 🧩 Domains | ⏳ |

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/hiveos/playground/playground.py` | PlaygroundEngine — validate/auto_agents/list_templates |
| `src/hiveos/brain/event_stream.py` | EventStream — agent lifecycle event pipeline |
| `src/hiveos/brain/decision_tracer.py` | DecisionTracer — decision path tracing |
| `src/hiveos/brain/approval_gate.py` | ApprovalGateEngine — human-in-loop gates |
| `src/hiveos/learning/logger.py` | ExecutionLogger — passive execution data collection |
| `src/hiveos/dashboard/server.py` | All API routes including new Playground/Brain/Learning |
| `tests/test_playground.py` | 14 tests for Playground module |
| `tests/test_brain.py` | 23 tests for Brain module |
| `tests/test_learning.py` | 14 tests for Learning module |
| `ROADMAP.md` | Roadmap with Phases 6/7/8 |
| `AGENTS.md` | This file — full project context |

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
python -m pytest tests/test_playground.py -v
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
| **2026-07-14** | **v0.7.0** | **Playground Core APIs + Brain Engine + Learning Logger (329 tests)** |
| **Next** | **v0.8.0** | **Playground Canvas + Runner + Gates UI + Brain 3D + Learning Analytics** |
| **2026-07-14** | **v0.8.0** | **Canvas+Viz Sprint: P-04 Flow Canvas, P-05 Runner+WS, P-06 Gates UI, B-05 3D Neural View, L-02 Analytics (366 tests)** |

---

## 🏁 Endgame Vision: HiveOS as a Windows Native Application

### The Product

HiveOS will ship as a **standard Windows desktop application** — installable via a proper MSI installer, with auto-update, beautiful UI, and a CI/CD pipeline.

### Architecture (Target)

```
┌─────────────────────────────────────────┐
│     Electron / Tauri Desktop Shell      │  ← Native window, system tray
│  ┌───────────────────────────────────┐  │
│  │  React / Svelte + Tailwind UI     │  │  ← Beautiful desktop UI
│  └──────────────┬────────────────────┘  │
│                 │ HTTP/WS               │
│  ┌──────────────▼────────────────────┐  │
│  │  Python (PyInstaller → .exe)      │  │  ← Embedded backend
│  │  FastAPI + Uvicorn                │  │
│  │  SQLite (hiveos.db)               │  │  ← All data persisted
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Roadmap to Windows Native

| Phase | What | Why |
|-------|------|-----|
| **Current** | FastAPI + Jinja2 SPA | Rapid prototyping, all features in browser |
| **Phase A** | Tauri shell wrapping the web UI | Native window, system tray, no browser tabs |
| **Phase B** | Replace Jinja2 with React/Svelte frontend | Desktop-grade UI with real components |
| **Phase C** | PyInstaller → single backend.exe | No Python dependency for users |
| **Phase D** | MSI installer (Inno Setup / WiX) | One-click install for Windows users |
| **Phase E** | Auto-updater (gh-release check on boot) | Users always on latest version |
| **Phase F** | CI/CD: GA test → build → sign → release | Automated delivery pipeline |

### Standards Checklist

- [x] **Semantic Versioning** (vX.Y.Z in pyproject.toml)
- [x] **Automated Tests** (366 pytest tests)
- [ ] **CHANGELOG.md** per release
- [x] **GitHub** (repo pushed)
- [ ] **GitHub Actions CI** (pytest on push)
- [ ] **Auto-updater** (checks GitHub Releases on startup)
- [ ] **Windows MSI installer**
- [ ] **Code signing** (Authenticode)
- [ ] **Beautiful desktop UI** (Tauri + React/Tailwind)
- [ ] **Persistent data** across restarts (SQLite — ✅ v0.9.0)

