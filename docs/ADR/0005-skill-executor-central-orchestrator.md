# ADR-0005: Skill Executor as Central Orchestrator

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

Skill execution involves multiple steps: loading definitions, retrieving knowledge, invoking capabilities, calling AI, validating outputs, recording history. Without a central orchestrator, this logic could scatter across components, creating multiple execution paths.

## Decision

The Skill Executor is the single, central orchestrator for all Skill executions. It handles the full lifecycle: load → validate → prepare (knowledge + capabilities) → compile prompt → invoke AI → parse output → record history → return result. Every Skill execution passes through this component, regardless of caller (Dashboard, Workflow Runner, Playground).

## Rationale

- Single execution path ensures consistent behavior, debugging, and auditing.
- Avoids the dual-engine problem (two parallel execution implementations).
- The Skill Executor interface is the most stable contract in the system — multiple components depend on it.

## Consequences

- Positive: One place to debug, one place to audit, one place to optimize.
- Positive: Adding new execution features (streaming, custom models) requires changing one component.
- Negative: The Skill Executor becomes a critical dependency. If it fails, no Skills run.
- Negative: Must resist temptation to add non-execution concerns to the Executor.

## References

- Product Decisions: PD-05
- Runtime Architecture §3 (Skill execution lifecycle)
- Skill Specification §5 (Skill lifecycle)
- Architecture Principles A1 (Single Execution Path)
