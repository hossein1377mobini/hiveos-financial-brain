# HiveOS — Agent Boot File

> Auto-loaded by Hermes when working in hive-os.
> Contains COMPLETE project state for cross-session continuity.
> Updated: 2026-07-24

---

## Identity

**HiveOS is an Organizational Intelligence Platform** that learns from organizations, reasons on their knowledge, and helps managers make better decisions.

**Source:** ADR-0017 (Product Direction Update)

---

## 4-Engine Architecture

```
Knowledge Engine → Learning Engine → Reasoning Engine → Decision Engine
```

| Engine | Responsibility |
|--------|---------------|
| **Knowledge Engine** | Domain Pack knowledge + Organization knowledge |
| **Learning Engine** | Continuous learning from files, events, user behavior |
| **Reasoning Engine** | AI-powered reasoning on knowledge (RAG, not training) |
| **Decision Engine** | Alerts, insights, recommendations for managers |

---

## Current Version: v1.0.0 (V1 Release)

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0-3 (Core) | ✅ | Foundation, Playground CLI, Integration, Packaging |
| Phase 4 (Mothership) | ✅ | Agent Registry, Task Router, Communication Bus |
| Phase 6 (Playground) | ✅ | Visual Builder + APIs |
| Phase 7 (Brain) | ✅ | Event Stream, Decision Tracer, Approval Gates |
| Phase 8 (Learning) | ✅ | Execution Logger + Analytics |
| Phase S (Storage) | ✅ | SQLite + Migrations |
| Phase CL (Standardisation) | ✅ | CHANGELOG + CI + Auto-update |
| Phase D (Domain) | ✅ | Domain CLI + Registry |
| Phase Desktop | ✅ | pywebview + PyInstaller + MSI |
| Phase PWA | ✅ | Installable Dashboard |
| Phase Playground UI | ✅ | React Flow Visual Builder |

---

## What Ships in V1

### Core Platform
- Domain Pack Manager (install, enable, disable, remove)
- Knowledge Service (unified search index)
- Skill Executor (load → knowledge → capabilities → AI → validate → record)
- AI Provider Interface (local default, cloud optional)
- Capability Service (KnowledgeSearch, FileReader, WebAccess, Calculator)
- Execution History Service (immutable audit)
- Workflow Runner (sequential Skill pipeline)
- Configuration Service
- Core API Gateway (HTTP/WebSocket)

### Domain Pack System
- Domain Pack Downloader (from remote registry)
- Domain Pack Manager (install, validate, enable, disable)
- Domain Pack Loader (parse YAML, validate structure)
- Domain Pack Registry (local catalog)

### Dashboard
- Searchable Knowledge Workspace
- Skill invocation
- Workflow execution
- Execution History view
- Domain Pack management
- File Watch (customer documents)

### Build & Distribution
- MSI Installer (Windows)
- PyInstaller .exe
- PWA (installable)
- Auto-Update Checker

### Accounting Domain Pack (D1)
- 200+ knowledge nodes (Persian)
- 29 agent blueprints
- 6 workflow templates
- 5 core skills

---

## Key Principles (ADR-0017)

1. **Organizational Learning ≠ Model Training** — RAG + Embeddings, not fine-tuning
2. **Privacy-First** — All data stays on customer infrastructure
3. **Decision Support** — Core differentiator, not just automation
4. **First-Time Experience** — No empty dashboard, immediate value
5. **Domain Packs = Knowledge + Capabilities** — Customer chooses what to activate
6. **Workflow Customization** — Customer adapts, HiveOS provides initial knowledge

---

## What's NOT in V1

- Model training / fine-tuning / LoRA
- Custom Workflow creation
- Pattern detection
- Analysis engine
- Recommendation engine
- Multi-domain orchestration
- Enterprise SSO / LDAP
- Two-way system integrations

---

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLite (WAL)
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, React Flow v12
- **Desktop:** pywebview, PyInstaller, MSI (Inno Setup)
- **Testing:** pytest, 436+ tests
- **CI/CD:** GitHub Actions

---

## Source Structure

```
hive-os/src/hiveos/
├── engine/       — Flow DSL, validator, executor
├── flow/         — Flow CLI commands
├── mothership/   — Agent registry, task router, comm bus, resilience, server
├── playground/   — Validation, auto-agent, templates, visual canvas, run/debug
├── brain/        — Event stream, decision tracer, approval gates
├── learning/     — Execution logger, analytics, pattern recognition
├── domain/       — Domain registry, CLI
├── domain_pack/  — Downloader, loader, manager, models, registry, validator
├── license/      — License models, manager
├── desktop/      — pywebview shell, PyInstaller
└── storage/      — SQLite StorageEngine, migrations
playground-ui/    — React Flow Visual Builder
```

---

## Roadmap (from ROADMAP.md)

| Version | Focus | Status |
|---------|-------|--------|
| **V1** | Core Intelligence Platform | **NOW** |
| V1.5 | Decision Support Foundation | NEXT |
| V2 | Intelligence Layer | FUTURE |
| V3 | Autonomous Intelligence | LONG TERM |

---

## Key Files

| File | Purpose |
|------|---------|
| `ROADMAP.md` | Product roadmap |
| `CHANGELOG.md` | Release history |
| `AGENTS.md` | This file |
| `docs/ADR/0017-product-direction-update.md` | Product direction decision |
| `docs/01-Product/` | 20 product documents |
| `docs/ADR/` | 17 Architecture Decision Records |

---

## Session History

| Date | Version | What Was Done |
|------|---------|---------------|
| 2026-07-13 | v0.1–0.5 | Foundation, Playground CLI, Integration, Packaging, Mothership |
| 2026-07-14 | v0.5–v0.12.0 | RBAC, Audit, Dashboard, Storage, Domain, Desktop, PWA, Playground UI |
| 2026-07-24 | v1.0.0 | Product Direction Update (ADR-0017), 4-Engine Architecture, Roadmap rewrite |
