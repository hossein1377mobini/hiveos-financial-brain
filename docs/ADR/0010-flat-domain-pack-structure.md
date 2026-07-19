# ADR-0010: Flat Domain Pack Directory Structure

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

Domain Packs contain knowledge, skills, workflows, and assets. The directory structure should be simple enough for humans to understand and machines to parse. Over-nesting adds complexity without proportional benefit in V1.

## Decision

V1 Domain Packs use a flat directory structure with maximum one level of nesting: `knowledge/`, `skills/`, `workflows/` as top-level directories, files directly inside each. No nested `assets/` directories. One `icon.png` at root.

## Rationale

- Flat structure is easy to understand, author, and parse.
- Nesting can be added backward-compatibly in future versions (a parser that reads directories of files will work with both flat and nested).
- V1 Domain Packs have ~5 Skills and ~20 knowledge files. No organizational need for subdirectories.

## Consequences

- Positive: Simple parser, easy to generate, easy to validate.
- Positive: Domain experts can understand the structure at a glance.
- Negative: Large future Domain Packs (50+ knowledge files) may need subdirectories for organization. This is backward-compatible.

## References

- Product Decisions: PD-10
- Domain Pack Specification §5
- Product Principles P1 (Simplicity)
