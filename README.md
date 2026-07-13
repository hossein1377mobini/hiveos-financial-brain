# HiveOS 🐝 — Multi-Agent Operating System

**Build complex agent workflows. Package them. Ship them anywhere.**

HiveOS is a platform for designing, deploying, and orchestrating Multi-Agent Systems (MAS). It turns a collection of AI agents into a structured, coordinated team — each with its own skills, knowledge, and role in a defined workflow.

## Why HiveOS?

Most agent frameworks stop at "one agent per task." HiveOS treats agents as **first-class OS processes**:

- 🧠 **Mothership Architecture** — one central orchestrator, many satellite nodes
- 📦 **Package & Deploy** — export an entire agent ecosystem and `hermes package install` it elsewhere
- 🔄 **Flow DSL** — declarative YAML to define agent teams, their roles, dependencies, and triggers
- 🗃️ **Enterprise Memory** — separate, structured, version-controlled knowledge base for the product itself
- 📡 **Communication Bus** — agents can message each other (and humans) across nodes

## Repository Structure

```
hive-os/
├── docs/               → Product knowledge base (opens as Obsidian vault)
│   ├── 01-Vision/      → Vision, market analysis, business model
│   ├── 02-Architecture/→ System architecture, ADRs, DSL spec
│   ├── 03-Flows/       → Workflow definitions and playground
│   ├── 04-Meetings/    → Session logs (all conversations)
│   ├── 05-Decisions/   → Key decisions with rationale
│   └── 06-Research/    → Market & technical research
├── prototype/          → Runnable prototypes and experiments
├── package/            → Package format spec and tooling
├── tools/              → CLI tooling around the ecosystem
├── ROADMAP.md          → Live roadmap
└── MANIFEST.md         → Product manifesto
```

## Status

**Phase 0 — Foundation** (active)
Designing the product knowledge base, flow DSL, and core architecture. All conversations are logged in `docs/04-Meetings/`.

## License

Proprietary — HiveOS Enterprise
