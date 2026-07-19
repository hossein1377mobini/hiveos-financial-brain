# ADR-0004: Capability Layer Between Knowledge and Skills

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

Skills need to perform system operations (search knowledge, read files, access web, compute calculations). Without a separate layer, each Skill would either reimplement these functions or contain imperative code to call system services.

## Decision

A Capability Layer sits between Knowledge and Skills. Capabilities are reusable system-level functions owned by the Core. Skills declare required capabilities by ID. The Skill Executor invokes capabilities through the Capability Service.

Knowledge → Capabilities → Skills → Workflows

## Rationale

- Prevents Skills from reinventing common system functions.
- Keeps Skills purely declarative (they say what they need, not how to do it).
- Enables capability reuse across multiple Skills and Domain Packs.
- Capabilities can be added or improved without modifying Skill definitions.

## Consequences

- Positive: Skill definitions are simpler and more focused.
- Positive: New system functions (OCR, database queries) become available to all Skills automatically.
- Negative: Requires up-front design of which capabilities exist and what interfaces they expose.
- Negative: Some flexibility is lost — Skills cannot implement custom system-level logic.

## References

- Product Decisions: PD-04
- Capability Layer Specification
- Skill Specification §3 (required_capabilities)
- Product Principles P3 (Modularity), P8 (Declarative)
