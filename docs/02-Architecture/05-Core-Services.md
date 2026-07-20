# 05 — Core Services

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Upstream Sources:** `docs/01-Product/10-Capability-Layer-Specification.md`, `docs/01-Product/11-AI-Provider-Specification.md`, `docs/01-Product/12-Execution-History-Specification.md`, `docs/01-Product/13-Skill-Specification.md`, `docs/01-Product/14-Workflow-Specification.md`, `docs/ADR/0003`, `0004`, `0005`, `0006`, `0007`, `0013`  
> **Dependencies:** 02-System-Architecture, 03-Runtime-Execution  
> **Priority:** 4  

---

## Purpose

Complete specification for every Core service. Each service gets: responsibility, boundaries, interface (methods with input/output schemas), dependencies, state (what it stores), error conditions, invariants, extension points. A developer implementing a service reads THIS document as their contract.

## Scope

**In:** Per-service interface definitions, method signatures, input/output schemas, state management, error conditions, invariants, extension points. All 9 Core services.

**Out:** HTTP endpoint contracts (06-API-Reference), shared data model schemas (07-Data-Models), configuration key definitions (09-Configuration).

## Table of Contents

```
1. Service Conventions
   1.1 Service Interface Template
   1.2 Error Handling (all services use ErrorEnvelope from 08)
   1.3 Logging Requirements
   1.4 Health Check Requirement (every service implements /health)

2. Core API Gateway
   2.1 Responsibility
   2.2 Boundaries
   2.3 Interface (route registration, middleware chain)
   2.4 Dependencies
   2.5 Error Conditions
   2.6 Invariants

3. Skill Executor
   3.1 Responsibility
   3.2 Boundaries
   3.3 Sub-Phases
       3.3.1 SkillLoader — load + parse Skill YAML
       3.3.2 InputValidator — validate against input_schema
       3.3.3 ContextBuilder — knowledge retrieval + capability invocation
       3.3.4 PromptCompiler — assemble prompt from instruction + context
       3.3.5 AIInvoker — call AI Provider Service
       3.3.6 OutputValidator — parse + validate against output_schema
       3.3.7 ExecutionRecorder — persist to Execution History Service
   3.4 Interface (execute_skill)
   3.5 Dependencies (Knowledge, Capability, AI Provider, History, Config)
   3.6 State (stateless — all state in Execution Context)
   3.7 Error Conditions
   3.8 Invariants
   3.9 Extension Points (custom validators, streaming)

4. Workflow Runner
   4.1 Responsibility
   4.2 Boundaries (does NOT implement Skill execution)
   4.3 Interface (execute_workflow)
   4.4 Dependencies (Skill Executor)
   4.5 State (stateless)
   4.6 Error Conditions (step failure = workflow failure in V1)
   4.7 Invariants
   4.8 Extension Points (branching, parallel, error handlers for V2)

5. Knowledge Service
   5.1 Responsibility
   5.2 Boundaries (read-only in V1, write stub for V2)
   5.3 Interface (search_knowledge, get_knowledge_by_id)
   5.4 V2 Stub (create_knowledge — returns not implemented)
   5.5 Dependencies (file system, search index)
   5.6 State (search index, source-tagged record metadata)
   5.7 Error Conditions
   5.8 Invariants (source tags never change, data never deleted)
   5.9 Extension Points (write path for V2, ontology merging)

6. Capability Service
   6.1 Responsibility
   6.2 Boundaries (does NOT implement business logic)
   6.3 Capability Registration
   6.4 Interface (invoke_capability, list_capabilities, get_capability)
   6.5 Core Capabilities (V1)
       6.5.1 core:knowledge_search
       6.5.2 core:file_reader
       6.5.3 core:calculator
       6.5.4 core:web_access
   6.6 Capability Interface Contract
   6.7 Dependencies (Knowledge Service for knowledge_search)
   6.8 State (capability registry — static)
   6.9 Error Conditions
   6.10 Invariants
   6.11 Extension Points (new capabilities, async execution in V2)

7. AI Provider Service
   7.1 Responsibility
   7.2 Boundaries (does NOT know about Skills, Domain Packs)
   7.3 Provider Interface (invoke)
   7.4 ProviderCapabilities (supports_streaming, supports_tools, etc.)
   7.5 Provider Adapters (V1)
       7.5.1 Local Model Adapter (Ollama/LM Studio)
       7.5.2 Cloud Model Adapter (OpenAI-compatible)
   7.6 Interface (invoke, get_provider_capabilities)
   7.7 Dependencies (Configuration Service)
   7.8 State (stateless)
   7.9 Error Conditions
   7.10 Invariants
   7.11 Extension Points (new adapters, streaming, tool calling)

8. Execution History Service
   8.1 Responsibility
   8.2 Boundaries (append-only, never modifies records)
   8.3 Interface (record_execution, get_execution, query_executions)
   8.4 Record Schema (see 07-Data-Models)
   8.5 Dependencies (persistent storage)
   8.6 State (execution records — append-only)
   8.7 Error Conditions
   8.8 Invariants
   8.9 Extension Points (analytics, pattern detection queries in V2)

9. Configuration Service
   9.1 Responsibility
   9.2 Boundaries (read-only for consumers, configurable by admin)
   9.3 Configuration Schema (see 09-Configuration)
   9.4 Interface (get_config, set_config)
   9.5 Dependencies (config file or DB)
   9.6 State (config key-value store)
   9.7 Error Conditions
   9.8 Invariants
   9.9 Extension Points (hot-reload, per-Business overrides)

10. Domain Pack Manager
    10.1 Responsibility
    10.2 Boundaries (does NOT execute packs)
    10.3 Interface (install, update, enable, disable, remove, list)
    10.4 Lifecycle Operations (see 04-Domain-Pack)
    10.5 Dependencies (file system, Configuration Service)
    10.6 State (pack registry, active/inactive status)
    10.7 Error Conditions
    10.8 Invariants
    10.9 Extension Points (multi-pack, marketplace integration)
```

## Estimated Size

~2,000 lines (largest document)

## Diagrams Required

- Skill Executor phase decomposition (block diagram)
- Capability Service registration → lookup → invocation flow

## Cross-References

| Target | Relationship |
|--------|-------------|
| 02-System-Architecture | Component map shows where these services live |
| 03-Runtime-Execution | Execution flow details are implemented by these services |
| 04-Domain-Pack-Specification | Domain Pack Manager and SkillLoader parse these formats |
| 06-API-Reference | External API calls route to these services |
| 07-Data-Models | All input/output schemas reference shared models |
| 08-Contracts | Error envelope, naming conventions required by all services |
| 09-Configuration | Configuration keys consumed by these services |
| docs/ADR/0003, 0004, 0005, 0006, 0007 | ADRs that constrain these services |

## Document Boundary Verification

This document defines WHAT each service does (interface, state, invariants). It does NOT define HOW execution flows through multiple services (03), what HTTP endpoints wrap these interfaces (06), or configuration key semantics (09). Service interface vs runtime orchestration vs API mapping — three distinct concerns, three documents.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
