# HiveOS — Agent Boot File 🐝

> This file is auto-loaded by Hermes when working in the hive-os project.
> It contains the COMPLETE project state so you never lose context between sessions.

---

## 📌 Current Phase: Phase 2 — Integration (Active)

Phase 0 (Foundation) ✅ | Phase 1 (Playground) ✅ | Phase 2 (Integration) 🔄

---

## 🎯 Immediate Next Task

**Connect Flow Engine → Hermes `delegate_task`**

File: `src/hiveos/engine.py` → method `_execute_agent()`

Currently uses a placeholder that prints "Agent completed" without actually running anything.
Replace it with a real `delegate_task` call that spawns a Hermes subagent with:
- The agent's `skills` loaded
- The agent's `knowledge` injected as context
- `input_from` data (from previous agents in the flow) passed as context
- Result captured as the agent's `output`

### Implementation approach:
```python
# In _execute_agent():
result = delegate_task(
    goal=f"Execute as agent '{agent.name}' with skills: {', '.join(agent.skills)}",
    context=f"""You are part of the HiveOS flow '{flow.name}'.
Previous agent output: {previous_output if agent.depends_on else 'none'}
Your task: Apply your skills ({', '.join(agent.skills)}) to process the input.
""",
    # Note: skills parameter is not supported by delegate_task directly
    # The agent's capabilities come from the context description
)
```

---

## 📋 Full State at Last Session (2026-07-13)

### What was built (v0.1.0)
| Component | File | Description |
|-----------|------|-------------|
| DSL Parser | `src/hiveos/dsl.py` | Flow, Agent, Trigger dataclasses + FlowDSL.load_flow() |
| Flow Engine | `src/hiveos/engine.py` | Topological sort, sequential agent execution, delivery |
| CLI | `src/hiveos/cli/main.py` | 8 commands: `flow run/validate/list`, `package build/install/list`, `util init/info` |
| Package Manager | `src/hiveos/package/__init__.py` | tar.gz builder + installer + manifest |
| Validator | `src/hiveos/utils/validator.py` | Full YAML schema validation |
| Config | `src/hiveos/utils/config.py` | ~/.hiveos/config.yaml |
| Knowledge | `src/hiveos/utils/knowledge.py` | KB scanner for docs/ |
| Hermes Skill | `hiveos-skill.md` | Installable skill for Hermes |
| Hello-flow | `prototype/hello-flow/hello.yml` | 3-agent flow demo |
| Package spec | `pyproject.toml` | Installable via `uv pip install .` |

### Latest commit
```
ae690aa docs: update roadmap - Phase 1 complete, Phase 2 current, add detail notes
6d28220 feat(core): HiveOS v0.1.0 - Flow Engine, CLI, Package Manager, DSL + first prototype flow
```
GitHub: `origin` → https://github.com/hossein1377mobini/hiveos-financial-brain.git

### Test results
- `hive util info` ✅
- `hive flow validate prototype/` ✅ (1 file valid)
- `hive flow run prototype/hello-flow/hello.yml` ✅ (3 agents executed in dependency order)
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
 ├── flow run <file>        — Validate + execute a flow
 ├── flow validate <dir>    — Bulk validate all YAML flows
 ├── flow list              — List available flows
 ├── package build <dir>    — Build tar.gz package
 ├── package install <file> — Install a package
 ├── package list           — List installed packages
 ├── util init              — Scaffold new HiveOS project
 └── util info              — Show environment
```

---

## 🎯 Full Task Backlog (for next sessions)

### Phase 2: Integration 🔄 (PRIORITY)
- [ ] **P1: Connect delegate_task** — replace placeholder in `_execute_agent()` with real Hermes `delegate_task`
- [ ] **State persistence** — flow state saved between agent steps (JSON/Redis)
- [ ] **Error handling** — agent failure → retry / reassign
- [ ] **Knowledge sync** — mothership pushes skills to satellites

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
