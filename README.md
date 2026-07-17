# HiveOS — Multi-Agent Operating System

**Core OS**: The pure agent orchestration platform.
**Knowledge Domains**: Sold separately — either pre-built (from our servers) or customer-provided (local path).

---

## What's In This Repo (Core OS)

| Directory | Purpose |
|-----------|---------|
| `src/` | Core engine — DSL, playground, domain registry, dashboard |
| `playground-ui/` | React Flow visual workflow builder (Node Palette, Properties Panel, Execution Trace) |
| `domains/` | Domain plugin definitions (blueprints, knowledge tree structure) |
| `docs/01-Vision/` | Product vision & direction |
| `docs/02-Architecture/` | Architecture docs & ADRs |
| `docs/06-Research/agents/` | Agent architecture research reference |
| `build/` | PyInstaller, installer, packaging |
| `tools/` | Utility tools |
| `tests/` | Test suite |

## What's NOT In This Repo (Knowledge Domains → Local/Separate)

- **Accounting Domain** → `D:\mind\knowledge\hiveos\accounting\` (local dev copy)
- Sold as a separate product: customer downloads from our server
- Or customer provides their own knowledge path

## Quick Start

```bash
hive desktop start     # Launch dashboard (port 9876)
hive playground        # Open Playground UI
hive domain register   # Register a knowledge domain
```

## Current Version

**v0.12.0** — Playground UI (React Flow visual builder)
- Linear-inspired dark-mode design (Inter font, brand indigo #5e6ad2)
- Node Palette — 16 nodes in 4 categories (Trigger/Action/AI/Flow Control)
- Properties Panel + Execution Trace + Mini-map + Controls
- Domain registry with blueprint system
- PWA installable dashboard
