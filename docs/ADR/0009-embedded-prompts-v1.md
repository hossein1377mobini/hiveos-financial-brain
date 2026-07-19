# ADR-0009: Embedded Prompts in V1 Skills

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

Skills contain AI prompts. These could be embedded inside the Skill YAML definition or stored as separate files with their own metadata, versioning, and localizations.

## Decision

In V1, prompts are embedded directly inside the Skill YAML `instruction` field. Separate prompt asset files are deferred to V2.

## Rationale

- V1 has ~5 Skills. Managing 5 separate prompt files alongside 5 Skill files doubles file count for no practical benefit.
- Refactoring 5 Skills when prompt extraction becomes necessary is an afternoon's work.
- The `instruction` field is clearly scoped within the Skill YAML — not mixed with other concerns.

## Consequences

- Positive: Simple, flat Skill definitions. One file per Skill.
- Negative: Multi-language prompt support requires refactoring every Skill file.
- Negative: Prompt versioning is tied to Skill versioning (cannot update prompt without updating Skill).

## References

- Product Decisions: PD-09
- Skill Specification §3 (instruction field)
- Deferred Decisions: DD-005
