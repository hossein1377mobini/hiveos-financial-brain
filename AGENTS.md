# HiveOS — Agent Boot File 🐝

> This file is auto-loaded by Hermes when working in the hive-os project.
> It contains the COMPLETE project state so you never lose context between sessions.

---

## 📌 Current Phase: Phase 5 — Enterprise ✅

Phase 0 (Foundation) ✅ | Phase 1 (Playground) ✅ | Phase 2 (Integration) ✅ | Phase 3 (Packaging) ✅ | Phase 4 (Mothership) ✅ | **Phase 5 (Enterprise) ✅** | **Phase D1 (Accounting) 🏗️**

---

## 🎯 Current Work: Phase D1 — Accounting Domain

- 💰 **Pricing model** — License tiers (✅ Complete — v0.6.0)
  - 4 tiers: Free, Pro, Enterprise, Ultimate
  - Feature flags with gating
  - Resource limits enforcement
  - Demo key activation
  - `hive license` CLI (info/activate/deactivate/upgrade/tiers/check)
  - Dashboard `/api/license` endpoint
  - 32 tests

### Phase D1: Next Steps
- 🏢 **Agent Blueprints** — YAML definitions in `domains/accounting/agents/blueprints/`
- 🔄 **Flow Templates** — YAML flows for common accounting workflows
- 🧠 **Hermes Skills** — Domain-specific knowledge prompts

---

## 📋 Session History

### v0.5.0 (2026-07-14) — Phase 5: Enterprise (RBAC) ✅

| Component | File | Description |
|-----------|------|-------------|
| RBAC Models | `src/hiveos/rbac/models.py` | Resource, Action, Permission, Role, User dataclasses + 4 built-in roles |
| RBAC Manager | `src/hiveos/rbac/manager.py` | YAML-backed persistence, authenticate(), check_permission(), full CRUD |
| RBAC Server Auth | `src/hiveos/mothership/server.py` | `_require_auth()` middleware on all HTTP endpoints, RBAC management API |
| RBAC CLI | `src/hiveos/cli/main.py` | `hive rbac user` (add/list/remove/set-role/set-api-key/enable/disable) + `hive rbac role` (add/list/show/remove) |
| RBAC tests | `tests/test_rbac.py` | 36 tests covering models, manager, permissions, persistence, auth |
| Test results | 160/160 | `python -m pytest tests/ -v` → 160 passed in 9.3s |

### v0.5.1 (2026-07-14) — Phase 5: Audit Trail ✅

| Component | File | Description |
|-----------|------|-------------|
| Audit Models | `src/hiveos/audit/models.py` | AuditEntry dataclass, AuditAction/Resource/Result enums, JSONL + gbrain markdown formats |
| Audit Trail | `src/hiveos/audit/trail.py` | JSONL daily files, local search, stats, rotate, gbrain sync (`gbrain put`), 20 tests |
| Server Audit | `src/hiveos/mothership/server.py` | `_audit_log()` middleware, logged on agent register/unregister, task assign/complete/fail, config updates, auth denials |
| Audit CLI | `src/hiveos/cli/main.py` | `hive audit list/search/stats/search-gbrain/sync-gbrain/rotate` |
| Audit tests | `tests/test_audit.py` | 20 tests covering models, JSONL persist, search, stats, rotate |
| Test results | 180/180 | `python -m pytest tests/ -v` → 180 passed in 9.6s |

### v0.4.0 (2026-07-14) — Phase 4: Mothership ✅

| Component | File | Description |
|-----------|------|-------------|
| Agent Registry | `src/hiveos/mothership/agent_registry.py` | Node registration, capability declaration, heartbeat monitoring, health checks |
| Task Router | `src/hiveos/mothership/task_router.py` | 5 routing strategies: BEST_FIT, LEAST_LOADED, ROUND_ROBIN, CAPABILITY_FIRST, AFFINITY |
| Communication Bus | `src/hiveos/mothership/communication_bus.py` | Pub/sub, request/response, 2 backends (InMemory + File-based) |
| Resilience Engine | `src/hiveos/mothership/resilience.py` | Health checker, failure detector, circuit breaker, task reassignment |
| Mothership Server | `src/hiveos/mothership/server.py` | FastAPI HTTP REST API for satellite communication |
| Mothership CLI | `src/hiveos/cli/main.py` | `hive mothership agent/route/bus/health/server` subcommands |
| Mothership tests | `tests/test_agent_registry.py`, `test_task_router.py`, `test_comm_bus.py`, `test_resilience.py` | 76 new tests |

### v0.3.0 (2026-07-13) — Phase 3: Package Registry ✅

| Component | File | Description |
|-----------|------|-------------|
| Package Registry | `src/hiveos/registry/registry.py` | YAML-based local catalog: publish, search, list, get latest, remove, install counter |
| Remote Registry Client | `src/hiveos/registry/remote.py` | HTTP client for remote registries: push/pull/search packages |
| Registry CLI | `src/hiveos/cli/main.py` | `hive registry list/search/info/remove/verify` |
| `hive package publish` | `src/hiveos/cli/main.py` | Build + publish in one command |
| Registry tests | `tests/test_registry.py` | 20 tests for registry, builder, installer, E2E |

### v0.2.0 (2026-07-13) — Phase 2: Integration ✅

| Component | File | Description |
|-----------|------|-------------|
| Node Registry | `src/hiveos/sync/node_registry.py` | YAML satellite node registration, heartbeat, CRUD |
| Sync Service | `src/hiveos/sync/sync_service.py` | tar.gz sync packages, HTTP push, dry-run |
| Mothership CLI | `src/hiveos/cli/main.py` | `hive mothership node/sync/info/preview` |
| Sync tests | `tests/test_sync.py` | 12 unit tests for NodeRegistry |

### Test results: 124/124 ✅
```
python -m pytest tests/ -v         → 124 passed in 9.3s
hive mothership agent list/info    → all working
hive mothership health status      → working
hive flow validate prototype/      → valid flows
hive registry list/search/info     → all working
```

---

## 🧩 Domain Plugin Architecture (NEW)

HiveOS is a **domain-agnostic OS** — any knowledge domain (accounting, medical, legal, engineering) can be installed as a domain plugin.

```
hive-os/
├── core/                      # Domain-agnostic (Flow Engine, Agent Registry, ...)
├── domains/                   # ★ Domain plugins
│   ├── accounting/            # First domain: Accounting & Finance
│   │   ├── domain.yaml        # Domain manifest
│   │   ├── knowledge/
│   │   │   ├── tree.yaml      # ★ Knowledge tree (10 branches, 200+ nodes)
│   │   │   └── references/    # Books, standards, laws
│   │   ├── agents/
│   │   │   └── blueprints/    # 24 agent blueprints
│   │   └── flows/             # 6 flow templates
│   └── <next-domain>/         # Future: Medical, Legal, ...
└── registry/                  # Domain package catalog
```

**Documents created this session:**
- `docs/01-Vision/02-domain-ecosystem-vision.md` — Multi-domain vision
- `docs/02-Architecture/03-domain-plugin-system.md` — Domain plugin architecture
- `domains/accounting/domain.yaml` — Accounting domain manifest (24 agents, 6 flows)
- `domains/accounting/knowledge/tree.yaml` — Full knowledge tree from official curricula

## 🏗️ Architecture at a Glance

```
User → Flow DSL YAML → Flow Engine (topological sort)
                         ├── Agent 1 (skills: A, B) ──┐
                         ├── Agent 2 (depends: 1) ───┤→ Hermes subagent (chat -q)
                         ├── Agent 3 (depends: 1) ───┘
                         └── Agent 4 (depends: 2, 3) → Final output → deliver
```

### CLI Structure
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
 └── util init/info
```

---

## 🎯 Full Task Backlog

### Phase 2: Integration ✅
- [x] P1: Connect Hermes subagent
- [x] P2: State persistence
- [x] P3: Error handling — retry, cascade skip, status tracking
- [x] P4: Knowledge sync — mothership pushes skills to satellites (via mothership sync)

### Phase 3: Packaging ✅
- [x] Package registry — YAML catalog for sharing packages
- [x] `hive package publish` — build + publish to registry
- [x] `hive registry` CLI — list, search, info, remove, verify
- [x] Remote Registry Client — HTTP client for remote registries

### Phase 4: Mothership ✅
- [x] Agent Registry — node registration, capability declaration, heartbeat monitoring
- [x] Task routing — 5 strategies: best-fit, least-loaded, round-robin, capability-first, affinity
- [x] Communication Bus — pub/sub messaging, request/response, two backends
- [x] Resilience — health checker, failure detection, circuit breaker, task reassignment
- [x] Mothership Server — FastAPI HTTP REST API for satellite nodes
- [x] Mothership CLI — `hive mothership` with 5 subcommand groups

### Phase 5: Enterprise 🏗️

- [x] **RBAC** — Role-based access control (models, manager, server auth, CLI, 36 tests)
- [ ] **Audit Trail** — Every action logged, traceable (uses gbrain PGLite)
- [ ] **Dashboard** — Web UI to monitor agents, flows, and nodes
- [ ] **Multi-tenant** — Isolated workspaces per team/org
- [ ] **Pricing model** — License tiers

---

## 🔧 Common Commands

```bash
cd "C:\Users\Hossein Mobini\Desktop\hive-os"
source .venv/Scripts/activate
uv pip install .                           # after code changes
.venv/Scripts/hive flow run prototype/hello-flow/hello.yml
.venv/Scripts/hive flow validate prototype/
.venv/Scripts/hive registry list
.venv/Scripts/hive registry search <query>
.venv/Scripts/hive registry verify
.venv/Scripts/hive mothership agent list
.venv/Scripts/hive mothership health status
.venv/Scripts/hive mothership server status
python -m pytest tests/ -v                 # run tests
git add -A && git commit -m "feat: ..." && git push origin master
```

---

## 📚 Key Files

| File | Path |
|------|------|
|| Product Vision | `docs/01-Vision/01-product-vision.md` |
|| High-Level Arch | `docs/02-Architecture/01-high-level-arch.md` |
|| Flow DSL Spec | `docs/02-Architecture/02-flow-dsl.md` |
|| ADR: File-Based Memory | `docs/02-Architecture/ADR/001-use-file-based-memory.md` |
|| Roadmap | `ROADMAP.md` |
|| Hermes Skill | `hiveos-skill.md` |
|| Prototype flows | `prototype/hello-flow/hello.yml`, `prototype/failure-test/error-handling.yml` |

### v0.5.2 (2026-07-14) — Phase 5: Dashboard ✅

| Component | File | Description |
|-----------|------|-------------|
| Dashboard Server | `src/hiveos/dashboard/server.py` | FastAPI-based REST API with 10 endpoints aggregating all subsystems |
| Dashboard UI | `src/hiveos/dashboard/templates/index.html` | Dark SPA with 8 views: Overview, Agents, Tasks, Health, Bus, Audit, RBAC, Domains |
| Dashboard CLI | `src/hiveos/cli/main.py` | `hive dashboard start/stop/status` commands |
| Dashboard tests | `tests/test_dashboard.py` | 23 tests covering API endpoints, server lifecycle, mock integration |
| Test results | 203/203 | `python -m pytest tests/ -v` → 203 passed in 11.7s |

### v0.5.3 (2026-07-14) — Phase 5: Multi-tenant ✅

| Component | File | Description |
|-----------|------|-------------|
| Workspace Models | `src/hiveos/workspace/models.py` | Workspace, WorkspaceSettings, WorkspaceMember, WorkspaceRole (5-level hierarchy) |
| Workspace Manager | `src/hiveos/workspace/manager.py` | YAML-backed CRUD, data isolation (agents/flows/audit/config dirs per workspace), member management |
| RBAC Integration | `src/hiveos/rbac/models.py` | User.workspace field for workspace-scoped identity |
| Workspace CLI | `src/hiveos/cli/main.py` | `hive workspace create/list/info/update/remove/activate` + `hive workspace member add/remove/set-role` |
| Dashboard API | `src/hiveos/dashboard/server.py` | `GET /api/workspaces` endpoint + workspace column in RBAC users table |
| Dashboard UI | `src/hiveos/dashboard/templates/index.html` | Workspaces tab in sidebar |
| Workspace tests | `tests/test_workspace.py` | 38 tests covering models, manager, members, RBAC integration |
| Test results | 241/241 | `python -m pytest tests/ -v` → 241 passed in 12.2s |
