# 08 — Contracts

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Dependencies:** 07-Data-Models (schemas referenced in conventions)  
> **Priority:** 5  

---

## Purpose

Service-to-service communication conventions. Defines the shared rules every service follows: error format, ID format, versioning strategy, timestamp format, pagination. A developer implementing any service reads this first to know the rules.

## Scope

**In:** Qualified ID format, error envelope, schema versioning strategy, timestamp format, pagination convention, truncation convention, naming conventions for services, capabilities, and packs.

**Out:** Service-specific interfaces (05), API endpoint contracts (06), data model schemas (07).

## Table of Contents

```
1. Format Conventions
   1.1 IDs: {domain_pack_id}:{resource_id}
   1.2 Capability IDs: core:{capability_name}@version
   1.3 Timestamps: ISO 8601 UTC
   1.4 Content-Type: application/json
   1.5 Encoding: UTF-8

2. Error Envelope
   2.1 Schema (see 07-Data-Models — ErrorEnvelope)
   2.2 Error Code Hierarchy
   2.3 Transient vs Permanent Errors
   2.4 When to Return Errors vs Exceptions

3. Schema Versioning
   3.1 Execution Context schema_version
   3.2 Forward Compatibility Rules
   3.3 Old Schema Handling

4. Pagination Convention
   4.1 Cursor-based vs Offset-based (V1: offset)
   4.2 Request Format
   4.3 Response Format

5. Truncation Convention
   5.1 Large Field Handling (content, ai_response)
   5.2 Truncation Indicator
   5.3 Reference Retrieval

6. Health Check Convention
   6.1 Every service implements GET /health
   6.2 Response Format
   6.3 Dependency Reporting

7. Naming Conventions
   7.1 Service names (PascalCase)
   7.2 Capability IDs (snake_case, namespaced)
   7.3 Skill IDs (kebab-case, within pack)
   7.4 Workflow IDs (kebab-case, within pack)
```

## Estimated Size

~400 lines

## Cross-References

| Target | Relationship |
|--------|-------------|
| 03-Runtime-Execution | Error propagation rules reference error envelope |
| 05-Core-Services | Every service implements these conventions |
| 06-API-Reference | API endpoints use error envelope |
| 07-Data-Models | ErrorEnvelope schema formally defined in 07 |

## Document Boundary Verification

This document defines SHARED RULES (naming, error format, timestamps). It does NOT define any service behavior, data shapes (those are in 07), or API contracts (06). Rules vs implementation: zero overlap.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
