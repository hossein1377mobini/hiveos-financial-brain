# Product Vision

## Elevator Pitch

HiveOS is a **Multi-Agent Operating System** — an open platform for defining, deploying, and orchestrating teams of AI agents across any number of machines. It wraps Hermes Agent into a structured, enterprise-grade multi-agent framework with a declarative flow DSL, package format, and mothership-satellite architecture.

## Problem Statement

Current AI agents are isolated:
- A single agent works alone, with no structured team collaboration
- Workflows are hard-coded or prompt-based, not declarative and version-controlled
- There is no standard way to package an agent ecosystem and move it between machines
- Enterprise teams have no visibility into what their agents are doing or how to coordinate them

## Solution

HiveOS introduces:

1. **Flow DSL** — a YAML-based language for defining agent teams, their roles, dependencies, triggers, and knowledge
2. **Flow Engine** — executes flows by spawning, coordinating, and monitoring agents through each step
3. **Package Format** — standard tar.gz that bundles flows, skills, knowledge, and config → portable agent ecosystem
4. **Mothership-Satellite** — one central orchestrator with distributed execution nodes
5. **Memory Vault** — enterprise-grade product knowledge base (this directory)

## Target Audience

| Segment | Need | Use Case |
|---------|------|----------|
| Solo developers | Reproducible agent workflows | Package their personal assistant ecosystem |
| Dev teams | Shared agent infrastructure | Standard flows for CI/CD, code review, deployment |
| Enterprise orgs | Scalable, auditable AI ops | Compliance, multi-tenant agent orchestration |
| AI consultants | White-label agent solutions | Ship pre-built agent packages to clients |

## Principles

- **Declarative over imperative** — define what, not how
- **Portable by default** — every flow is a package
- **Observable** — all agent actions logged and traceable
- **Resilient** — node failures don't lose work
