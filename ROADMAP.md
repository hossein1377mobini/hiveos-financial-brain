# HiveOS Roadmap 🗺️

Live product roadmap. Updated after every session.

---

## Phase 0: Foundation ⏳ (Current)

| Task | Status | Notes |
|------|--------|-------|
| Product KB structure | ✅ Done | docs/ directory as Obsidian vault |
| Separate memory system | ✅ Done | Dedicated from main Obsidian vault |
| Kickoff session log | ✅ Done | 2026-07-13 Meeting Note #001 |
| Git init & version control | ⏳ Pending | |
| Hermes skill for HiveOS | ⏳ Pending | |
| Daily log cron | ⏳ Pending | |

## Phase 1: Playground (Next)

- [ ] **Flow DSL v0.1** — YAML schema for agent team definitions
- [ ] **Flow Engine** — Hermes-based executor that runs a flow via delegate_task chain
- [ ] **Playground demo** — 2-agent flow (research → summarize → deliver to TG)
- [ ] **State persistence** — Flow state saved between steps
- [ ] **Error handling** — Agent failure → retry / reassign

## Phase 2: Packaging

- [ ] **Package spec** — Tar.gz format for agent ecosystems
- [ ] `hermes package export` — Export flows + skills + knowledge
- [ ] `hermes package install` — Import on another Hermes node
- [ ] **Package registry** — Central hub to discover/shared packages

## Phase 3: Mothership

- [ ] **Agent Registry** — Node registration, capability declaration
- [ ] **Knowledge sync** — Mothership pushes skills to satellites
- [ ] **Task routing** — Route tasks by capability + load
- [ ] **Communication Bus** — Cross-node agent messaging
- [ ] **Resilience** — Node failure → task reassignment

## Phase 4: Enterprise

- [ ] **RBAC** — Role-based access control on flows
- [ ] **Audit trail** — Every action logged, traceable
- [ ] **Dashboard** — Web UI to monitor agents, flows, and nodes
- [ ] **Multi-tenant** — Isolated workspaces per team/org
- [ ] **Pricing model** — License tiers
