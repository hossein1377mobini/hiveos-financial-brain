---
name: hiveos
description: "HiveOS - Multi-Agent Operating System skill for Hermes Agent"
version: 0.1.0
author: HiveOS Team
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [multi-agent, orchestration, flow-dsl, package-management, enterprise]
    homepage: https://github.com/hossein1377mobini/hiveos-financial-brain
    related_skills: [hermes-agent]
---

# HiveOS Skill

This skill provides integration between Hermes Agent and HiveOS - the Multi-Agent Operating System.

## Capabilities

- **Flow DSL Management** - Create, validate, and execute Flow DSL YAML files
- **Agent Orchestration** - Coordinate multi-agent workflows through Hermes delegate_task
- **Package Management** - Build, install, and distribute HiveOS packages
- **Mothership-Satellite** - Set up distributed agent execution across nodes

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

## Flow DSL Quick Reference

```yaml
name: "Weekly Research Digest"
description: "Research trending AI topics → write digest → publish to Telegram"
version: "0.1.0"

trigger:
  cron: "0 9 * * 1"

agents:
  - id: researcher
    name: "Research Agent"
    skills:
      - arxiv
      - web-search
    knowledge:
      - topics.md
    output: research_findings.md

  - id: writer
    name: "Content Writer"
    depends_on:
      - researcher
    skills:
      - content-creation
    input_from:
      agent: researcher
      files: [research_findings.md]
    output: draft.md

deliver:
  to: origin
  format: markdown
```

## Integration with Hermes

This skill enables:
1. **delegate_task spawning** - Each agent in a flow runs as a Hermes delegate_task
2. **Skill loading** - Agents load their required skills from the HiveOS knowledge base
3. **Memory sharing** - Flow state persists across agent executions
4. **Gateway delivery** - Final output delivered through Hermes gateway to Telegram, Discord, etc.

## Installation

```bash
# From local path
hermes skills install C:\Users\Hossein Mobini\Desktop\hive-os

# Or from GitHub (when published)
hermes skills install hossein1377mobini/hiveos
```

## Usage Example

```bash
# Create a new flow
mkdir my-flow
cat > my-flow/flow.yml << 'EOF'
name: "My First Flow"
description: "Hello HiveOS"
version: "0.1.0"
trigger:
  type: "manual"
agents:
  - id: greeter
    name: "Greeter"
    skills: ["text-generation"]
    output: "greeting.txt"
deliver:
  to: "telegram:me"
EOF

# Run it
hive run my-flow/flow.yml
```

## Project Structure

```
hive-os/
├── src/hiveos/         # Python package
│   ├── dsl.py          # Flow DSL definitions
│   ├── engine.py       # Flow execution engine
│   ├── cli.py          # CLI commands
│   └── package/        # Package management
├── prototype/          # Example flows
├── tools/              # CLI tooling
└── docs/               # Knowledge base (Obsidian vault)
```

## Development

```bash
# Install in development mode
cd C:\Users\Hossein Mobini\Desktop\hive-os
pip install -e .

# Run tests
python -m pytest tests/

# Build package
python -m build
```