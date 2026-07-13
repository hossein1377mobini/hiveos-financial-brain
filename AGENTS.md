# HiveOS — Agent Boot File 🐝

> This file is auto-loaded by Hermes when working in the hive-os project.
> It contains the COMPLETE project state so you never lose context between sessions.

---

## 📌 Current Phase: Phase 3 — Package Registry (Complete ✅)

Phase 0 (Foundation) ✅ | Phase 1 (Playground) ✅ | Phase 2 (Integration) ✅ | Phase 3 (Packaging) ✅ | **Phase 4 (Mothership) 🔜**

---

## 🎯 Next Up: Phase 4 — Mothership

File: `src/hiveos/mothership/`

- **Agent Registry** — node registration, capability declaration
- **Task routing** — route tasks by capability + load
- **Communication Bus** — cross-node agent messaging
- **Resilience** — node failure → task reassignment

---

## 📋 Session History

### v0.4.0 (2026-07-13) — Phase 3: Package Registry ✅

| Component | File | Description |
|-----------|------|-------------|
| Package Registry | `src/hiveos/registry/registry.py` | YAML-based local catalog: publish, search, list, get latest, remove, install counter |
| Remote Registry Client | `src/hiveos/registry/remote.py` | HTTP client for remote registries: push/pull/search packages |
| Registry CLI | `src/hiveos/cli/main.py` | `hive registry list/search/info/remove/verify` |
| `hive package publish` | `src/hiveos/cli/main.py` | Build + publish in one command |
| Registry tests | `tests/test_registry.py` | 20 tests for registry, builder, installer, E2E |

### v0.3.0 (2026-07-13) — Phase 2: Integration ✅

| Component | File | Description |
|-----------|------|-------------|
| Node Registry | `src/hiveos/sync/node_registry.py` | YAML satellite node registration, heartbeat, CRUD |
| Sync Service | `src/hiveos/sync/sync_service.py` | tar.gz sync packages, HTTP push, dry-run |
| Mothership CLI | `src/hiveos/cli/main.py` | `hive mothership node/sync/info/preview` |
| Sync tests | `tests/test_sync.py` | 12 unit tests for NodeRegistry |

### Test results: 48/48 ✅
```
hive flow validate prototype/      → 2 valid flows
hive package publish . --name hiveos-core → published
hive registry list/search/info/verify → all working
python -m pytest tests/ -v         → 48 passed in 8.6s
```

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
 ├── flow run/validate/list/state/clear-state
 ├── package build/install/list/publish
 ├── registry list/search/info/remove/verify
 ├── mothership node/sync/preview/info
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

### Phase 4: Mothership 🔜 (Next)
- [ ] Agent Registry — node registration, capability declaration
- [ ] Task routing — route by capability + load
- [ ] Communication Bus — cross-node agent messaging
- [ ] Resilience — node failure → task reassignment

### Phase 5: Enterprise
- [ ] RBAC, Audit trail, Dashboard, Multi-tenant, Pricing

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
python -m pytest tests/ -v                 # run tests
git add -A && git commit -m "feat: ..." && git push origin master
```

---

## 📚 Key Files

| File | Path |
|------|------|
| Product Vision | `docs/01-Vision/01-product-vision.md` |
| High-Level Arch | `docs/02-Architecture/01-high-level-arch.md` |
| Flow DSL Spec | `docs/02-Architecture/02-flow-dsl.md` |
| ADR: File-Based Memory | `docs/02-Architecture/ADR/001-use-file-based-memory.md` |
| Roadmap | `ROADMAP.md` |
| Hermes Skill | `hiveos-skill.md` |
| Prototype flows | `prototype/hello-flow/hello.yml`, `prototype/failure-test/error-handling.yml` |
