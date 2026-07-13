# HiveOS — Agent Boot File 🐝

> This file is auto-loaded by Hermes when working in the hive-os project.
> It contains the COMPLETE project state so you never lose context between sessions.

---

## 📌 Current Phase: Phase 3 — Package Registry (Active)

Phase 0 (Foundation) ✅ | Phase 1 (Playground) ✅ | Phase 2 (Integration) ✅ | Phase 3 (Package Registry) 🔄

---

## 🎯 Current: Phase 3 — Package Registry (Active 🔄)

Phase 0 (Foundation) ✅ | Phase 1 (Playground) ✅ | Phase 2 (Integration) ✅ | Phase 3 (Package Registry) 🔄

---

### ✅ Completed this session (2026-07-13 v0.4.0)

| Component | File | Description |
|-----------|------|-------------|
| Package Registry | `src/hiveos/registry/registry.py` | YAML-based local catalog: publish, search, list, get latest version, remove, install counter |
| Remote Registry Client | `src/hiveos/registry/remote.py` | HTTP client for remote registries: push/pull/search packages |
| `hive registry` CLI | `src/hiveos/cli/main.py` | `hive registry list/search/info/remove/verify` commands |
| `hive package publish` | `src/hiveos/cli/main.py` | Build + publish to local registry in one command |
| Registry tests | `tests/test_registry.py` | 17 tests covering RegistryEntry, PackageRegistry, PackageBuilder, PackageInstaller, and E2E workflow |

### CLI Commands Added

```
hive registry list [--tag]          — List published packages
hive registry search <query>        — Search by name/desc/tag/author
hive registry info <name> [version] — Show package details
hive registry remove <name>         — Remove from registry
hive registry verify                — Check registry integrity
hive package publish <dir>          — Build + publish to registry
```

### Test results: 48/48 ✅
- All 31 existing tests + 17 new registry tests pass

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

### Phase 3: Packaging (Completed ✅)
- [x] Package registry — central hub for sharing packages
- [x] `hive package publish` command
- [x] `hive registry` CLI (list/search/info/remove/verify)
- [x] Remote registry client (push/pull/search)

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
