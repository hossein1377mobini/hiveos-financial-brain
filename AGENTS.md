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
| Phase 6 (Playground) | ✅ Full (APIs + Canvas + Runner) | v0.8.0 |
| Phase 7 (Brain) | ✅ Full (Engine + API + 3D Viz) | v0.8.0 |
| Phase 8 (Learning) | ✅ Full (Logger + Analytics) | v0.8.0 |
| Phase S (Storage) | ✅ SQLite Persistence | v0.9.0 |
| **CL (Standardisation)** | **🏗️ CHANGELOG + CI** | **v0.9.0** |

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

## ✅ What's Built (v0.9.0 — 379 tests)

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

### ✅ Phase 6: Playground — Full (v0.8.0)
| Task | Status | Description |
|------|--------|-------------|
| **P-01** `POST /api/playground/validate` | ✅ | Flow YAML validation with rich errors/warnings |
| **P-02** `POST /api/playground/auto-agents` | ✅ | Task description → auto-select domain agents (keyword scoring) |
| **P-03** `GET /api/playground/templates` | ✅ | Browse domain flow templates with metadata |
| **P-04** Visual Canvas (HTML5 Canvas in Dashboard) | ✅ | Drag & drop flow builder |
| **P-05** `POST /api/playground/run` + WS streaming | ✅ | Async execution + WebSocket event stream |

### ✅ Phase 7: Brain — Full (v0.8.0)
| Task | Status | Description |
|------|--------|-------------|
| **B-01** Event Stream Pipeline | ✅ | Agent lifecycle events with filtering + stats |
| **B-02** Decision Tracer | ✅ | Trace every decision path + step tracking |
| **B-03** Approval Gate Engine | ✅ | Create/approve/reject/expire gates with stats |
| **B-04** Brain API (REST) | ✅ | All routes: /api/brain/events, /traces, /gates |
| **B-05** 3D Neural View (Three.js/WebGL) | ✅ | Interactive agent topology visualization |

### ✅ Phase 8: Learning — Full (v0.8.0)
| Task | Status | Description |
|------|--------|-------------|
| **L-01** Execution Logger | ✅ | Passive in-memory collection + stats + trends |
| **L-02** Execution Analytics | ✅ | Trend analysis, bottleneck detection, failure patterns |

### ✅ Phase S: Storage — SQLite Persistence (v0.9.0)
| Task | Status | Description |
|------|--------|-------------|
| **S-01** StorageEngine (SQLite) | ✅ | Generic key-value store, WAL mode, thread-safe |
| **S-02** Brain persistence | ✅ | EventStream, DecisionTracer, ApprovalGateEngine persist to SQLite |
| **S-03** Learning persistence | ✅ | ExecutionLogger logs survive restarts |
| **S-04** Playground persistence | ✅ | FlowRunner state saved/restored |
| **S-05** Data directory init | ✅ | `~/.hiveos/data/` auto-created on first run and via `hive util init` |

### ✅ CL: Standardisation (v0.9.2)
| Task | Status | Description |
|------|--------|-------------|
| **CL-01** CHANGELOG.md | ✅ | Keep a Changelog format |
| **CL-02** CI (GA pytest on push) | ✅ | `.github/workflows/test.yml` |
| **CL-03** Auto-update skeleton | ✅ | `hive update check/info`, GitHub Releases checker |

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

## 🎯 Next: Phase D1 — Accounting Domain + Storage Improvements

### What to Build Next

| Priority | Task | Layer | Status |
|----------|------|-------|--------|
| 🟡 | **P-07** Template Customizer | 🎮 Playground | ⏳ |
| 🟡 | **P-08** Flow Library (save/share user flows) | 🎮 Playground | ⏳ |
| 🟢 | **D-04** Hermes skills for accounting agents | 🧩 Domains | ⏳ |
| 🟢 | **D-05** Domain Plugin CLI (`hive domain list/info/install`) | 🧩 Domains | ⏳ |
| 🟢 | **S-06** Migration system for StorageEngine | 🗄️ Storage | ⏳ |
| 🟢 | **CL-03** Auto-update skeleton | 🔧 Standardisation | ✅ |
| ⬜ | **v0.10.0** Windows Native Sprint (Tauri shell) | 🪟 All | ⏳ |

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
| **2026-07-14** | **v0.9.1** | **S-05 data dir init + CL-02 CI + version fixes + S-06 migrations + D-05 domain CLI + D-04 Hermes skills (413 tests)** |
| **Next** | **v0.9.2** | **CL-03 Auto-update skeleton** |
| **Next** | **v0.10.0** | **Windows Native Sprint (Tauri shell)** |

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

