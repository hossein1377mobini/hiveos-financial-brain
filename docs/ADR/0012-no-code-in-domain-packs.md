# ADR-0012: No Executable Code in Domain Packs

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

Domain Packs could theoretically contain executable code (Python scripts, shell commands, compiled binaries) for custom logic. This would increase expressiveness but introduce security, portability, and authorship risks.

## Decision

Domain Packs contain zero executable code. Only declarative content (YAML, Markdown, structured data). This is an absolute prohibition, not a guideline.

## Rationale

- Security: Executable code in packs creates a supply chain attack surface. A malicious pack could compromise the entire HiveOS installation.
- Portability: Code couples packs to a specific runtime. A Python-based pack breaks if the Core changes its execution environment.
- Authorship: Domain experts cannot author packs that require code. Requiring engineering skills for pack creation contradicts the product vision.
- Boundary clarity: The Core/Application boundary is clean only if the Application (Domain Pack) cannot modify Core behavior through code.

## Consequences

- Positive: Domain Packs are safe to install from any source. No sandboxing, no code review for safety.
- Positive: Domain experts can author packs independently.
- Negative: Some domain logic that requires custom computation must be implemented as a Core Capability instead. This means the Capability Service must be sufficiently expressive.
- Negative: V1's limited Capability set may constrain pack authors (addressed by expanding Capabilities in V2).

## References

- Product Decisions: PD-01, PD-12
- Domain Pack Specification §3
- Product Principles P8 (Declarative over Imperative)
