# HiveOS — Agent Boot File 🐝

> This file is auto-loaded by Hermes when working in the hive-os project.
> It contains the COMPLETE project state so you never lose context between sessions.

---

## 📌 Current Phase: Phase 2 — Integration (Active)

Phase 0 (Foundation) ✅ | Phase 1 (Playground) ✅ | Phase 2 (Integration) 🔄

---

## 🎯 Immediate Next Task

**Phase 3: Packaging** — Package registry, `hive package publish`, central hub for sharing packages

File: `src/hiveos/package/__init__.py` + new `src/hiveos/registry/`

- Package registry service to publish/discover packages
- `hive package publish` command to push to registry
- Central hub for sharing agent ecosystems across teams

---

## 📋 Full State at Last Session (2026-07-13)

### What was built (v0.3.0)

Added in this session:
| Component | File | Description |
|-----------|------|-------------|
| Node Registry | `src/hiveos/sync/node_registry.py` | YAML-based satellite node registration, heartbeat, CRUD |
| Sync Service | `src/hiveos/sync/sync_service.py` | Builds tar.gz sync packages (skills+knowledge+flows), HTTP push to satellites, dry-run preview |
| Mothership CLI | `src/hiveos/cli/main.py` | `hive mothership node register/list/remove`, `hive mothership sync` (`--dry-run`), `hive mothership info`, `hive mothership preview` |
| Sync tests | `tests/test_sync.py` | 12 unit tests for NodeRegistry CRUD and persistence |

### Test results (31/31 ✅)
- `hive flow validate prototype/` ✅ (2 valid flows)
- `python -m pytest tests/ -v` ✅ 31 passed in 8s

### Full file map

---

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
 ├── flow run <file>            — Validate + execute a flow
 ├── flow run <file> --resume   — Resume from last saved state
 ├── flow validate <dir>        — Bulk validate all YAML flows
 ├── flow list                  — List available flows
 ├── flow state [file]          — Show persisted state for a flow (or list all)
 ├── flow clear-state <file>    — Delete persisted state for a flow
 ├── package build <dir>        — Build tar.gz package
 ├── package install <file>     — Install a package
 ├── package list               — List installed packages
 ├── util init                  — Scaffold new HiveOS project
 └── util info                  — Show environment
```

---

## 🎯 Full Task Backlog

### Phase 2: Integration 🔄 (PRIORITY)
- [x] **P1: Connect Hermes subagent**
- [x] **P2: State persistence**
- [x] **P3: Error handling** — retry, cascade skip, status tracking
- [ ] **P4: Knowledge sync** — mothership pushes skills to satellites

### Phase 3: Packaging (future)
- [ ] Package registry — central hub for sharing packages
- [ ] `hive package publish` command

### Phase 4: Mothership (future)
- [ ] Agent Registry — node registration, capability declaration
- [ ] Task routing — route by capability + load
- [ ] Communication Bus — cross-node messaging
- [ ] Resilience — node failure → task reassignment

### Phase 5: Enterprise (future)
- [ ] RBAC, Audit trail, Dashboard, Multi-tenant, Pricing

---

## 🔧 Common Commands

```bash
# Activate
cd "C:\Users\Hossein Mobini\Desktop\hive-os"
source .venv/Scripts/activate

# Reinstall after code changes
uv pip install .

# Run a flow
.venv/Scripts/hive flow run prototype/hello-flow/hello.yml

# Validate all flows
.venv/Scripts/hive flow validate prototype/

# Run tests
python -m pytest tests/ -v

# Push changes
git add -A && git commit -m "feat: message" && git push origin master
```

---

## 📚 Key Files & Where They Live

| File | Path |
|------|------|
| Product Vision | `docs/01-Vision/01-product-vision.md` |
| High-Level Arch | `docs/02-Architecture/01-high-level-arch.md` |
| Flow DSL Spec | `docs/02-Architecture/02-flow-dsl.md` |
| ADR: File-Based Memory | `docs/02-Architecture/ADR/001-use-file-based-memory.md` |
| Accounting MAS Report | `docs/06-Technical/HiveOS-Accounting-Multi-Agent-Architecture-Report.md` |
| Accounting KB (Persian) | `docs/06-Research/accounting/` |
| Roadmap | `ROADMAP.md` |
| Manifesto | `MANIFEST.md` |
| Hermes Skill | `hiveos-skill.md` |
| Meeting Log | `docs/04-Meetings/` |
| Prototype flows | `prototype/hello-flow/hello.yml`, `prototype/failure-test/error-handling.yml` |
