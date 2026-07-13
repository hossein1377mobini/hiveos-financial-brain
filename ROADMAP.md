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

## Phase 2: Integration (Current 🔄)

- [x] CLI tooling for packaging & running flows
- [x] Hermes skill for HiveOS
- [x] **Flow Engine → Hermes subagent** — real subprocess spawning
- [x] **State persistence** — resume support, state CLI
- [x] **Error handling** — retry, cascade skip, status tracking
- [ ] **Knowledge sync between Mothership and satellites**

## Phase 3: Packaging

- [ ] **Package spec finalized** — Tar.gz format for agent ecosystems
- [ ] `hive package export` — Export flows + skills + knowledge
- [ ] `hive package install` — Import on another Hermes node
- [ ] **Package registry** — Central hub to discover/share packages

## Phase 4: Mothership

- [ ] **Agent Registry** — Node registration, capability declaration
- [ ] **Knowledge sync** — Mothership pushes skills to satellites
- [ ] **Task routing** — Route tasks by capability + load
- [ ] **Communication Bus** — Cross-node agent messaging
- [ ] **Resilience** — Node failure → task reassignment

## Phase 5: Enterprise

- [ ] **RBAC** — Role-based access control on flows
- [ ] **Audit trail** — Every action logged, traceable
- [ ] **Dashboard** — Web UI to monitor agents, flows, and nodes
- [ ] **Multi-tenant** — Isolated workspaces per team/org
- [ ] **Pricing model** — License tiers
