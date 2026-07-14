---
name: hiveos
description: "HiveOS - Multi-Agent Operating System with Playground, Brain visualization, and Domain plugins"
version: 0.6.0
author: HiveOS Team
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [multi-agent, orchestration, flow-dsl, playground, brain, domain-plugins, accounting]
    homepage: https://github.com/hossein1377mobini/hiveos-financial-brain
    related_skills: [hermes-agent]
---

# HiveOS Skill — Multi-Agent Operating System

**HiveOS is a platform for designing, deploying, and orchestrating teams of AI agents through a visual Playground, monitored by a 3D Brain, and powered by pluggable domain knowledge.**

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         🧠 BRAIN                            │
│              3D Neural Visualization — Glass Box            │
├──────────────────────────────────────────────────────────────┤
│                         🎮 PLAYGROUND                       │
│          Visual Flow Builder — Drag, Drop, Configure        │
├──────────────────────────────────────────────────────────────┤
│                         🔧 ENGINE                           │
│  CLI • Flow Engine • Mothership • RBAC • Audit • Workspace  │
├──────────────────────────────────────────────────────────────┤
│                         🧩 DOMAINS                          │
│           Accounting (D1) • Medical • Legal • ...           │
└──────────────────────────────────────────────────────────────┘
```

## Current State: v0.6.0

### ✅ Built (273 tests)
- Flow Engine, Mothership, Agent Registry, Task Router
- Communication Bus, Resilience Engine
- Package Registry (local + remote)
- RBAC (36 tests), Audit Trail (20 tests)
- Dashboard FastAPI + SPA (23 tests)
- Multi-tenant Workspaces (38 tests)
- License Pricing tiers (32 tests)
- Accounting Domain: 29 agent blueprints + 6 flow templates

### 🏗️ Next: Phase 6 — Playground Core APIs
- `POST /api/playground/validate` — validate flow YAML
- `POST /api/playground/auto-agents` — task → auto agent team
- `GET /api/templates/` — browser domain templates
- React Flow visual canvas
- Run/Debug with WebSocket streaming

### 🧠 Next: Phase 7 — Brain
- Agent event stream pipeline
- Decision path tracer
- Approval gate engine
- 3D neural WebGL visualization

## CLI Commands

```bash
hive --version                              # v0.6.0
hive flow run <flow.yml>                    # Execute a flow
hive flow validate <dir>                    # Validate flow YAMLs
hive license info                           # Show license
hive license activate <key>                 # Activate tier
hive dashboard start                        # Start web UI
hive mothership server start                # Start mothership
# ... see README.md for full reference
```

## Commands

```bash
# Run a flow
hive run <flow-file.yml>

# Package an ecosystem
hive package <source-dir> --output <package.tar.gz>

# Inspect a package
hive inspect <package-name>

# Start server
hive serve --port 8080
```

## Installation

```bash
# From local path
hermes skills install C:\Users\Hossein Mobini\Desktop\hive-os

# Or from GitHub
hermes skills install hossein1377mobini/hiveos
```

## Project Structure

```
hive-os/
├── src/hiveos/                 # Python package
│   ├── cli/main.py             # CLI entry point
│   ├── engine.py               # Flow engine
│   ├── license/                # Pricing & feature gating
│   ├── rbac/                   # Role-based access
│   ├── audit/                  # Audit trail
│   ├── dashboard/              # Web UI + Playground
│   ├── workspace/              # Multi-tenant
│   ├── mothership/             # Agent registry, router, bus, resilience
│   └── ...                     # Registry, sync, package, utils
├── domains/                    # ★ Domain plugins
│   └── accounting/             # First domain
│       ├── domain.yaml         # 29 agents, 6 flows
│       ├── knowledge/tree.yaml # 200+ node tree
│       ├── agents/blueprints/  # 29 YAML blueprints
│       └── flows/              # 6 YAML templates
├── docs/                       # Knowledge base
├── tests/                      # 273 tests
├── ROADMAP.md                  # Full roadmap
├── AGENTS.md                   # Full project context
└── README.md / README.fa.md    # Bilingual docs
```

## Development

```bash
cd C:\Users\Hossein Mobini\Desktop\hive-os
source .venv/Scripts/activate
uv pip install -e .
python -m pytest tests/ -v
```
