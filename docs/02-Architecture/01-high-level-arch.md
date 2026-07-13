# High-Level Architecture

## Overview

```
┌─────────────────────────────────────────────────────────┐
│                      MOTHERSHIP                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Registry │  │ Flow     │  │ Knowledge             │  │
│  │ Manager  │  │ Engine   │  │ Distributor           │  │
│  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘  │
│       │              │                   │              │
│  ┌────▼──────────────▼───────────────────▼──────────┐  │
│  │            Communication Bus (Message Queue)      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────┬──────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Node A   │   │ Node B   │   │ Node C   │
    │ (Sat.)   │   │ (Sat.)   │   │ (Sat.)   │
    └──────────┘   └──────────┘   └──────────┘
```

## Layers

### 1. Mothership (Orchestrator)
- **Registry Manager** — tracks every node: address, capabilities, status, assigned flows
- **Flow Engine** — reads Flow DSL YAML → spawns agents → chains outputs → handles errors
- **Knowledge Distributor** — syncs skills, knowledge bases, and config to satellites
- **Communication Bus** — message queue (NATS/RabbitMQ/Redis) for agent ↔ agent and node ↔ node messaging

### 2. Satellite Nodes (Hermes Instances)
Each satellite is a standard Hermes agent instance running:
- Assigned flows
- Required skills (synced from mothership)
- Task queue for incoming assignments
- Heartbeat to mothership

### 3. Communication Bus
- Agent-to-agent messaging (within & across nodes)
- Task assignments and results
- Knowledge sync events
- Heartbeat / health checks
- Currently: gateway + webhook-based. Future: NATS.

## Data Flow

```
1. User defines a flow → Flow DSL YAML
2. User triggers flow → Flow Engine parses & schedules
3. Engine spawns Agent 1 (Hermes delegate_task) → Agent 1 gets context + skills
4. Agent 1 completes → output stored in flow state
5. Engine spawns Agent 2 → gets Agent 1's output as context
6. ... chain continues until flow complete
7. Final output delivered to configured destination (TG, Slack, etc.)
```

## Key Design Decisions

- **Hermes is the runtime** — every agent runs as a Hermes session (or delegate_task). We don't build a new agent framework; we build the orchestration layer on top.
- **Skill-based knowledge** — each agent's capability comes from loaded skills, not hard-coded prompts
- **File-based memory** — the product KB is markdown files (version-controllable, portable, Obsidian-viewable)
