# ADR-0002: Execution Over Learning in V1

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

HiveOS's long-term vision includes pattern detection, recommendation, and continuous learning. However, V1 has no customers and no usage data. Building learning infrastructure before there is data to learn from is premature optimization.

## Decision

V1 ships execution history collection only. Pattern detection, recommendation engine, confidence scoring, and learning from rejection are deferred to V2.

Execution History collects: every Skill and Workflow execution with full context (inputs, outputs, prompts, responses, duration, errors, knowledge retrieved). This data is persisted immutably.

## Rationale

- Learning requires data. V1 has no data. Building pattern detection is building a telescope before there is light.
- Execution History serves immediate V1 needs: debugging, audit, and transparency.
- Execution History is the necessary foundation for V2 learning. Without it, V2 cannot detect patterns.
- Removing learning scope from V1 reduces engineering effort by ~40%.

## Consequences

- Positive: V1 is simpler, faster to build, and focused on productivity value.
- Positive: Execution History data collected during V1 will enable rich V2 learning.
- Negative: V1 cannot claim "self-learning" capability. Marketing must focus on productivity, not intelligence.
- Negative: If Execution Context design misses signals needed for V2 learning, retrofitting will be painful.

## References

- Product Decisions: PD-02
- Product Scope: V1 section, V2 section
- Execution History Specification
- Product Principles P1 (Simplicity), P4 (Practical Value)
