# 07 — Data Models

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Upstream Sources:** `docs/ADR/0011`  
> **Dependencies:** 05-Core-Services (interface definitions reference these models)  
> **Priority:** 5  

---

## Purpose

Every shared data structure in the system, defined in JSON Schema format. Source of truth for what every record looks like across all states. A developer implementing any service references this document for all data shapes.

## Scope

**In:** JSON Schema definitions for every shared data model. Field descriptions, types, defaults, nullable status, versioning strategy.

**Out:** How data flows through execution (03-Runtime-Execution), storage implementation details.

## Table of Contents

```
1. Schema Conventions
   1.1 Format (JSON Schema Draft 2020-12)
   1.2 Required vs Optional
   1.3 Nullable Convention
   1.4 Schema Versioning
   1.5 Extensibility (additionalProperties)

2. ExecutionContext
   2.1 schema_version: integer
   2.2 id, type, skill_id, workflow_id, status
   2.3 timestamps block
   2.4 input_parameters
   2.5 knowledge_retrieved (with reference_id strategy)
   2.6 capability_results
   2.7 prompt_sent
   2.8 ai_response (with reference_id strategy)
   2.9 output
   2.10 errors (ErrorEnvelope[])

3. ExecutionRecord
   3.1 id, type, skill_id, workflow_id, pack_id
   3.2 timestamps (started, completed, duration_ms)
   3.3 ai metadata (provider, model, prompt_version)
   3.4 input_parameters, output
   3.5 status
   3.6 knowledge references
   3.7 errors

4. SkillDefinition
   4.1 id, name, description, version
   4.2 input_schema
   4.3 output_schema
   4.4 knowledge_requirements (tags, concepts)
   4.5 required_capabilities (qualified IDs)
   4.6 model configuration block
   4.7 instruction (prompt)

5. WorkflowDefinition
   5.1 id, name, description, version
   5.2 steps (ordered array)
   5.3 step: id, skill_id, input_mapping, on_error (V1: fail only)
   5.4 output_mapping

6. DomainPackMetadata
   6.1 id, version, name, description
   6.2 min_core_version
   6.3 core_api_version
   6.4 author
   6.5 skill_ids[]
   6.6 workflow_ids[]

7. KnowledgeDocument
   7.1 id, source_type, source_id
   7.2 content, format
   7.3 tags[], metadata{}, immutable, created_at

8. CapabilityResult
   8.1 capability_id
   8.2 input, output
   8.3 duration_ms
   8.4 error (optional)

9. AIProviderResponse
   9.1 content
   9.2 model_used
   9.3 usage (prompt_tokens, completion_tokens, total_tokens)
   9.4 duration_ms
   9.5 error (optional)

10. ErrorEnvelope
    10.1 code, message, details, transient

11. HealthStatus
    11.1 status, version, uptime_seconds, dependencies[]
```

## Estimated Size

~600 lines

## Cross-References

| Target | Relationship |
|--------|-------------|
| 03-Runtime-Execution | Execution Context lifecycle uses these models |
| 04-Domain-Pack-Specification | Skill/Workflow/Knowledge schemas are formalized here |
| 05-Core-Services | All service interfaces reference these models |
| 06-API-Reference | API request/response bodies are composed from these models |
| 08-Contracts | ErrorEnvelope, naming conventions, versioning strategy |

## Document Boundary Verification

This document defines STATIC data shapes (what every record looks like). It does NOT define how records are used in execution (03), what API endpoints return them (06), or storage implementation. Schema vs lifecycle vs transport — three distinct concerns.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
