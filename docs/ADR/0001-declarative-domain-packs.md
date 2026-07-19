# ADR-0001: Use Declarative Domain Packs

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

Domain Packs deliver industry-specific content to HiveOS installations. We need a distribution format that is safe, portable, and authorable by domain experts who are not software engineers.

Options considered: executable code (Python packages), declarative content (YAML/Markdown), database dumps, custom binary format.

## Decision

Domain Packs will be purely declarative. They contain YAML manifests, Markdown knowledge documents, and structured Skill/Workflow definitions. No executable code of any kind. No scripts, no compiled binaries, no plugins.

## Rationale

- Security: Declarative packs have no execution surface. A malicious pack cannot execute arbitrary code.
- Portability: A directory of files can be copied between installations, version-controlled, and inspected.
- Authorability: Domain experts can author packs without engineering skills. YAML and Markdown are accessible.
- Platform independence: Declarative packs do not depend on a specific runtime, language, or OS.

## Consequences

- Positive: Domain Packs are safe to install from any source. No sandboxing needed.
- Positive: Domain Pack creation does not require a software development kit.
- Negative: Some domain logic may be inexpressible without code. This forces a clean boundary — if it requires code, it belongs in the Core as a Capability, not in the Domain Pack.
- Negative: The Core must provide sufficient Capabilities for Skills to express their full range of behavior.

## Alternatives Considered

- **Python packages:** Rejected due to security risk and domain expert authorship barrier.
- **Database dumps:** Rejected due to lack of version control and inspectability.
- **Custom binary format:** Rejected due to complexity and tooling requirements.

## References

- Product Decisions: PD-01, PD-12
- Domain Pack Specification §3, §4
- Architecture Principles A3 (Declarative Boundaries)
- Product Principles P8 (Declarative over Imperative)
