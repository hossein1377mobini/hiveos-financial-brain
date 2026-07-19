# ADR-0007: Single Knowledge Index with Source Tagging

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

HiveOS manages two types of knowledge: Domain Knowledge (from Domain Packs, read-only) and Organization Knowledge (customer-specific, mutable). The Product Bible requires separation for upgrade safety. The question is how to handle this in V1.

Options: separate indexes with merge layer, single index with source tags, hybrid approach.

## Decision

Use a single searchable knowledge index. Every document is tagged with its source type: `domain:` for Domain Pack content, `org:` for organization-owned content. Source tagging is a metadata field on each document, not a separate store.

## Rationale

- V1 does not need the complexity of a merge layer. A single index with tags is simple to implement.
- Source tags preserve the conceptual separation. The Knowledge Service can filter by source when needed.
- If V2 requires full separation, the tags enable a migration path (split index by tag).
- Merge infrastructure (dedup, conflict resolution, precedence) is not needed with one Domain Pack.

## Consequences

- Positive: Simple, fast, buildable in days.
- Positive: Domain Pack upgrades don't affect organization-tagged content.
- Negative: If source tagging was designed wrong, splitting later could be expensive. Mitigation: tag format is `{source_type}:{id}` — extensible by design.
- Negative: Performance characteristics differ from separate indexes (larger index, but simpler code).

## References

- Product Decisions: PD-07
- Domain Pack Specification §8 (content ownership)
- Product Principles P3 (Modularity)
- Architecture Principles A10 (Storage Separation)
