# ADR-0011: Execution Context Object

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

A Skill or Workflow execution produces and consumes data across multiple steps: inputs, knowledge, capability results, prompts, AI responses, outputs, errors. This data must flow through the execution, be available for audit, and be persisted as execution history.

## Decision

Every execution (Skill or Workflow) creates an Execution Context object. The Execution Context is the single container for all state produced during execution. It flows through the entire lifecycle. The complete Execution Context is persisted by the Execution History Service at the end of execution.

## Rationale

- Single source of truth for a given execution. No scattered state across components.
- Simplifies debugging — the Execution Context contains everything needed to understand what happened.
- Directly feeds the Execution History Service — no need to assemble data from multiple sources for audit.
- Enables execution replay, error investigation, and future pattern detection from a single data structure.

## Consequences

- Positive: Complete audit trail without additional effort.
- Positive: Debugging and development (Playground) benefit from full execution visibility.
- Negative: Execution Context size grows with knowledge retrieved and AI response length. Storage must handle variable-size records.
- Negative: Must define the Execution Context schema early — changing it later breaks history compatibility.

## References

- Product Decisions: PD-11
- Runtime Architecture §3 (Execution Context)
- Execution History Specification §2 (record structure)
- Skill Specification §5 (Skill lifecycle)
