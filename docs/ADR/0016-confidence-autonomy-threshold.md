# ADR-0016: Confidence-Based Autonomy Threshold

**Status:** Deferred
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

As pattern detection (V2+) improves, some patterns may be detected with very high confidence (e.g., "this transaction pattern has been observed 5,000 times across 50 employees with zero exceptions"). Requiring human validation for every such pattern creates unnecessary friction.

## Decision

Deferred to V2+. HiveOS V1 never changes organizational behavior automatically. The question of whether and how confidence-based autonomous adoption should work is deferred until pattern detection exists and we have empirical data on its precision.

## Rationale

- Cannot design autonomous adoption without knowing pattern detection quality. We need data first.
- False positives at low confidence would erode trust before any autonomy is granted.
- The autonomy threshold design (confidence level, override mechanism, audit trail, rollback capability) is a complex interaction between trust, UX, and accountability.
- V1's principle (humans always validate) is the safe default. Relaxing it later is easier than tightening it.

## Trigger for Revisit

- Pattern detection precision exceeds 95% in empirical testing.
- Customer demand for reduced manual review overhead.
- Clear understanding of the consequences of false positives vs false negatives at different confidence levels.

## ADR Converted from ADC

- Original: ADC-001 (Architectural Decision Candidate from Product Discovery)
- Recorded to ensure this question is not lost during V2 design.

## References

- Product Bible §6 (Human Ownership)
- Product Principles P2 (Human Ownership), P5 (Augment First)
- Deferred Decisions: DD-001
- ADR-0015 (Human Ownership of Business Truth)
