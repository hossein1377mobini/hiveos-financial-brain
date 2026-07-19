# ADR-0015: Human Ownership of Business Truth

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

The product philosophy establishes that HiveOS never owns business truth. Humans do. This principle has concrete architectural implications.

## Decision

The system never changes business rules autonomously. Every recommendation for organizational knowledge, Skills, or Workflows requires explicit human validation before being adopted. Disagreement between system and human is treated as a learning mechanism, not a failure mode.

Architectural implications:
- Skill execution produces recommendations, not decisions.
- Workflows include human checkpoints for critical actions.
- Execution History captures user feedback (when provided).
- Pattern validation (V2+) is always a human-in-the-loop workflow.

## Rationale

- Core philosophical principle. Trust is earned through transparency and human control.
- Prevents the system from amplifying its own errors by adopting false patterns.
- Disagreement data (human rejected → system learned boundary) is essential for V2 learning quality.
- Regulatory compliance (financial, legal domains) requires human oversight of automated decisions.

## Consequences

- Positive: Users trust the system because they control all changes.
- Positive: Rejected recommendations provide high-quality training data for V2 learning.
- Negative: Every pattern adoption requires human effort. At scale (hundreds of recommendations), this creates review bottlenecks.
- Negative: Future confidence-based autonomy (DD-001) will require revisiting this principle with clear thresholds.

## References

- Product Decisions: PD-15
- Product Bible §6 (Core Philosophy)
- Product Principles P2 (Human Ownership), P5 (Augment First)
- Deferred Decisions: DD-001
