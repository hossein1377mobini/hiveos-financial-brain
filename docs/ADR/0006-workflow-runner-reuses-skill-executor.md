# ADR-0006: Workflow Runner Reuses Skill Executor

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

Workflows execute multiple Skills in sequence. Without a clear architectural boundary, the Workflow Runner could implement its own Skill execution logic — creating a second, parallel execution path and duplicating the dual-engine problem.

## Decision

The Workflow Runner does NOT implement Skill execution logic. It is a pure orchestrator. For each step, it calls the Skill Executor with the step's skill_id and prepared inputs. The Skill Executor handles all execution details.

## Rationale

- Preserves the single execution path (Architecture Principle A1).
- Eliminates duplication of execution logic.
- Any enhancement to Skill execution (streaming, new capabilities) automatically benefits Workflows.
- Workflow Runner's responsibility is limited to sequencing and data mapping.

## Consequences

- Positive: Consistent behavior between single-Skill and Workflow execution.
- Positive: Workflow Runner is simpler (no AI interaction, no capability orchestration).
- Negative: Workflow Runner cannot optimize across steps (e.g., parallel execution without Skill Executor involvement).
- Negative: Adding cross-step features (shared context, aggregated results) requires Skill Executor interface changes.

## References

- Product Decisions: PD-06
- Workflow Specification §2, §5
- Runtime Architecture §3 (Workflow execution)
- Architecture Principles A1 (Single Execution Path)
