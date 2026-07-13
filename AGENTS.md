# HiveOS — Agent Boot File 🐝

> This file is auto-loaded by Hermes when working in the hive-os project.
> It contains the COMPLETE project state so you never lose context between sessions.

---

## 📌 Current Phase: Phase 2 — Integration (Active)

Phase 0 (Foundation) ✅ | Phase 1 (Playground) ✅ | Phase 2 (Integration) 🔄

---

## 🎯 Immediate Next Task

**P3: Error handling** — agent failure → retry / reassign

File: `src/hiveos/engine.py`

Currently agents fail silently with non-zero returncode. Add:
- Configurable retry count (already in Agent DSL: `retry` field)
- `n_retries` counter in agent result
- On final failure, skip agent or reassign to next available agent

---

## 📋 Full State at Last Session (2026-07-13)

### What was built (v0.1.0)
| Component | File | Description |
|-----------|------|-------------|
| DSL Parser | `src/hiveos/dsl.py` | Flow, Agent, Trigger dataclasses + FlowDSL.load_flow() |
| Flow Engine | `src/hiveos/engine.py` | Topological sort, sequential agent execution via Hermes `chat -q` subprocess, delivery, **state persistence** |
| State Persistence | `src/hiveos/engine.py` | `_save_state()` / `_load_state()` / `clear_state()` — JSON at `~/.hiveos/flows/<flow_name>/state.json`, auto-save after each agent, `--resume` flag |
| CLI | `src/hiveos/cli/main.py` | 11 commands: `flow run/validate/list/state/clear-state`, `package build/install/list`, `util init/info` |
| Package Manager | `src/hiveos/package/__init__.py` | tar.gz builder + installer + manifest |
| Validator | `src/hiveos/utils/validator.py` | Full YAML schema validation |
| Config | `src/hiveos/utils/config.py` | ~/.hiveos/config.yaml |
| Knowledge | `src/hiveos/utils/knowledge.py` | KB scanner for docs/ |
| Hermes Skill | `hiveos-skill.md` | Installable skill for Hermes |
| Hello-flow | `prototype/hello-flow/hello.yml` | 3-agent flow demo (tested: 3 Hermes subagents spawned) |
| Package spec | `pyproject.toml` | Installable via `uv pip install .` |

### Latest commit
```
0ebcd87 feat(core): connect Flow Engine to Hermes subagent via chat -q
```
GitHub: `origin` → https://github.com/hossein1377mobini/hiveos-financial-brain.git

### Test results
- `hive util info` ✅
- `hive flow validate prototype/` ✅ (1 file valid)
- `hive flow run prototype/hello-flow/hello.yml` ✅ (3 Hermes subagents spawned in sequence: Greeter→Personalizer→Deliverer, 173s total)
- `hive flow list` ✅
- Package build tested ✅ (CLI works)

### Workspace
- `.venv/` — venv with uv (Python 3.11.7)
- `~/.hiveos/config.yaml` — auto-generated with defaults

---

## 🏗️ Architecture at a Glance

```
User → Flow DSL YAML → Flow Engine (topological sort)
                         ├── Agent 1 (skills: A, B) ──┐
                         ├── Agent 2 (depends: 1) ───┤→ Hermes delegate_task
                         ├── Agent 3 (depends: 1) ───┘
                         └── Agent 4 (depends: 2, 3) → Final output → Telegram/Discord/etc
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

## 🎯 Full Task Backlog (for next sessions)

### Phase 2: Integration 🔄 (PRIORITY)
- [x] **P1: Connect Hermes subagent** — replaced placeholder in `_execute_agent()` with real `hermes chat -q` subprocess spawning
- [x] **P2: State persistence** — flow state saved between agent steps in `~/.hiveos/flows/<flow_name>/state.json`, auto-persist after each agent, `--resume` flag, `flow state`, `flow clear-state`
- [ ] **P3: Error handling** — agent failure → retry / reassign
- [ ] **P4: Knowledge sync** — mothership pushes skills to satellites

### Phase 3: Packaging (future)
- [ ] Package registry — central hub for sharing packages
- [ ] `hive package publish` command

### Phase 4: Mothership (future)
- [ ] Agent Registry — node registration, capability declaration
- [ ] Task routing — route by capability + load
- [ ] Communication Bus — cross-node messaging (NATS/Redis)
- [ ] Resilience — node failure → task reassignment

### Phase 5: Enterprise (future)
- [ ] RBAC, Audit trail, Dashboard, Multi-tenant, Pricing

---

## 🔧 Common Commands

```bash
# Activate
cd "C:\Users\Hossein Mobini\Desktop\hive-os"
.venv/Scripts/activate

# Reinstall after code changes
uv pip install .

# Run a flow
.venv/Scripts/hive flow run prototype/hello-flow/hello.yml

# Validate
.venv/Scripts/hive flow validate prototype/

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
| Accounting KB (Persian) | `docs/06-Research/accounting/01-اصول-حسابداری/001-mabani-accounting.md` |
| Roadmap | `ROADMAP.md` |
| Manifesto | `MANIFEST.md` |
| Hermes Skill | `hiveos-skill.md` |
| Meeting Log | `docs/04-Meetings/` |
