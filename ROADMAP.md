# HiveOS Roadmap 🗺️

Live product roadmap. Updated after every session.

---

## Phase 0: Foundation ✅ (Complete)

| Task | Status | Notes |
|------|--------|-------|
| Product KB structure | ✅ Done | docs/ directory as Obsidian vault |
| Separate memory system | ✅ Done | Dedicated from main Obsidian vault |
| Kickoff session log | ✅ Done | 2026-07-13 Meeting Note #001 |
| Git init & version control | ✅ Done | GitHub: hossein1377mobini/hiveos-financial-brain |
| Hermes skill for HiveOS | ✅ Done | `hiveos-skill.md` – installable via hermes skills install |
| Python package (pyproject.toml) | ✅ Done | Installable with `uv pip install .` |
| Flow DSL + Validator | ✅ Done | YAML schema, structural validation |
| Flow Engine | ✅ Done | Topological sort, sequential agent execution |
| CLI (hive flow/package/util) | ✅ Done | 8 subcommands, all functional |
| Hello-flow prototype | ✅ Done | 3-agent flow with dependency chain |
| Package builder/installer | ✅ Done | tar.gz format, manifest.yaml |

## Phase 1: Playground ✅ (Complete)

| Task | Status | Notes |
|------|--------|-------|
| Flow DSL v0.1 | ✅ Done | YAML schema for agent team definitions |
| Flow Engine | ✅ Done | Hermes-based executor via delegate_task chain |
| Playground demo | ✅ Done | 3-agent flow (greeter → personalizer → deliverer) |
| State persistence | ✅ Done | Flow state saved between steps |
| Error handling | ✅ Done | Agent failure → retry / reassign / cascade skip, flow-level status tracking |

## Phase 2: Integration ✅

- [x] CLI tooling for packaging & running flows
- [x] Hermes skill for HiveOS
- [x] **Flow Engine → Hermes subagent** — real subprocess spawning
- [x] **State persistence** — resume support, state CLI
- [x] **Error handling** — retry, cascade skip, status tracking
- [x] **Knowledge sync between Mothership and satellites**

## Phase 3: Packaging ✅

- [x] **Package spec finalized** — Tar.gz format for agent ecosystems
- [x] `hive package publish` — Publish to local registry
- [x] `hive registry` — List, search, info, remove, verify commands
- [x] **Package registry** — Central hub to discover/share packages
- [x] **Remote Registry Client** — HTTP client for remote registries

## Phase 4: Mothership ✅

- [x] **Agent Registry** — Node registration, capability declaration, heartbeat monitoring
- [x] **Task routing** — 5 strategies: BEST_FIT, LEAST_LOADED, ROUND_ROBIN, CAPABILITY_FIRST, AFFINITY
- [x] **Communication Bus** — Pub/sub, request/response, in-memory + file-based backends
- [x] **Resilience** — Health checker, failure detection, circuit breaker, task reassignment
- [x] **Mothership Server** — FastAPI HTTP REST API for satellite communication
- [x] **Mothership CLI** — `hive mothership` with agent/route/bus/health/server subcommands

## Phase 5: Enterprise ✅

- [x] **RBAC** — Role-based access control (models, manager, server auth, CLI, 36 tests)
- [x] **Audit Trail** — JSONL daily files + gbrain PGLite sync (CLI, server middleware, 20 tests)
- [x] **Dashboard** — Web UI to monitor agents, flows, and nodes
- [x] **Multi-tenant** — Isolated workspaces per team/org
- [x] **Pricing model** — License tiers (Free, Pro, Enterprise, Ultimate) with feature gating

---

## 🎯 Domain System Phases (NEW)

### Phase D1: Accounting Domain 🏗️
- [x] Knowledge tree from official curricula (Bachelor's 1404 + Master's 1402)
- [x] Domain manifest (domain.yaml) with 24 agent blueprints
- [x] Domain plugin architecture docs (vision + arch)
- [ ] Agent blueprints (YAML definitions in `agents/blueprints/`)
- [ ] Flow templates (YAML flows for common accounting workflows)
- [ ] Hermes skills for each agent (domain-specific knowledge prompts)

### Phase D2: Domain Plugin System (⏳ Planned)
- [ ] `hive domain` CLI (list, info, install, remove, init)
- [ ] Domain registry (discover/shared domains)
- [ ] Domain loading in Mothership
- [ ] Cross-domain dependency resolution

### Phase D3: Next Domain (⏳ Planned)
- [ ] Choose next domain (medical, legal, engineering, ...)
- [ ] Build its knowledge tree + agents + flows
- [ ] Publish to domain registry
