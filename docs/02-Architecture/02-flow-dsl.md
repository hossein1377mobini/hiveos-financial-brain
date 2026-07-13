# Flow DSL Specification (Draft v0.1)

The Flow DSL is a YAML-based language for defining multi-agent workflows. Each flow describes a team of agents, their roles, dependencies, triggers, knowledge, and delivery.

## Example

```yaml
name: "Weekly Research Digest"
description: "Research trending AI topics → write digest → publish to Telegram"
version: "0.1.0"

# Trigger: when and how the flow starts
trigger:
  cron: "0 9 * * 1"   # weekly on Monday 9am
  # event: "webhook:research-complete"  (future)

# All agents in this flow
agents:
  - id: researcher
    name: "Research Agent"
    skills:
      - arxiv
      - web-search
      - literature-review
    knowledge:
      - topics.md          # shared context file
      - interests.md       # user preferences
    output: research_findings.md
    # deliver: telegram:me  (optional per-agent delivery)

  - id: writer
    name: "Content Writer"
    depends_on:
      - researcher        # waits for researcher to complete
    skills:
      - content-creation
      - markdown
    knowledge:
      - brand-voice.md
    input_from:
      agent: researcher
      files: [research_findings.md]
    output: draft.md

  - id: publisher
    name: "Publisher"
    depends_on:
      - writer
    skills:
      - wordpress-admin
      - social-publishing
    action:
      publish:
        to: [wordpress, telegram]
      notify: true

# Shared memory/state for the flow
memory:
  share_context: true
  consolidate: weekly
  trace: true               # log every step for audit

# Delivery of final output
deliver:
  to: origin               # back to the chat that triggered it
  format: markdown
```

## Schema (v0.1)

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Human-readable flow name |
| `description` | string | - | What this flow does |
| `version` | semver | ✅ | Flow DSL version |
| `trigger` | object | - | How the flow starts (cron/event/manual) |
| `agents` | array[Agent] | ✅ | Agent team definition |
| `memory` | object | - | Shared memory configuration |
| `deliver` | object | - | Final output delivery |

### Agent Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique agent identifier in this flow |
| `name` | string | - | Display name |
| `skills` | array[string] | ✅ | Skills to load for this agent |
| `knowledge` | array[string] | - | Knowledge files to inject |
| `depends_on` | array[string] | - | Agents to wait for before starting |
| `input_from` | object | - | Where to get input from prior agents |
| `output` | string | - | File to write agent output to |
| `action` | object | - | Specific actions beyond generate |
| `deliver` | object | - | Per-agent delivery override |
| `timeout` | int | - | Max minutes before timeout (default: 10) |
| `retry` | int | - | Retry attempts on failure (default: 2) |

## Flow Engine (Future Implementation)

The Engine:
1. **Parse** — reads YAML, validates against schema
2. **Resolve** — builds dependency graph, identifies critical path
3. **Schedule** — determines execution order (parallelizable agents run concurrently)
4. **Execute** — spawns Hermes delegate_tasks per agent in order
5. **Monitor** — tracks status, handles failures
6. **Deliver** — sends final output to configured destinations
7. **Log** — writes trace log to `docs/04-Meetings/flow-runs/`
