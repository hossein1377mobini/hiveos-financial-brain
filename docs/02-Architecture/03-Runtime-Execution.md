# 03 — Runtime Execution

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Upstream Sources:** `docs/01-Product/08-Runtime-Architecture.md`, `docs/ADR/0005`, `0006`, `0011`  
> **Dependencies:** 02-System-Architecture  
> **Priority:** 3  

---

## Purpose

Complete execution lifecycle for Skills and Workflows. Defines how a request flows from entry point through all participating services to response. Specifies state transitions, timeout handling, error propagation, and execution context lifecycle. A developer implementing the Skill Executor or Workflow Runner follows this document.

## Scope

**In:** Skill execution state machine, Workflow execution state machine, Execution Context lifecycle (creation → population → persistence), timeout policy, error propagation rules, retry semantics (V1: none — fail immediately), streaming path (V1: not supported, placeholder for V2), sequence diagram for every execution scenario.

**Out:** Service interface definitions (delegated to 05), Domain Pack format (delegated to 04), data model schemas (delegated to 07).

## Figure of Contents

```
1. Skill Execution
   1.1 State Machine
        CREATED → VALIDATING → PREPARING (Knowledge + Capabilities)
        → COMPILING → INVOKING → PARSING → RECORDING → COMPLETED
        Any state → FAILED (exception, timeout, validation error)
   1.2 Phase-by-Phase Specification
       1.2.1 Load Skill Definition
       1.2.2 Validate Input Parameters
       1.2.3 Retrieve Knowledge
       1.2.4 Invoke Pre-AI Capabilities
       1.2.5 Compile AI Prompt
       1.2.6 Invoke AI Provider
       1.2.7 Parse and Validate Output
       1.2.8 Invoke Post-AI Capabilities
       1.2.9 Record Execution History
   1.3 Timeout Policy
       (total timeout, per-phase timeout, configurable)
   1.4 Error Propagation
       (which errors are terminal, which are recoverable)
   1.5 Retry Semantics (V1: none)

2. Workflow Execution
   2.1 State Machine
        CREATED → RUNNING (N steps) → COMPLETED
        Any step FAILED → WORKFLOW_FAILED
   2.2 Step-by-Step Specification
       2.2.1 Load Workflow Definition
       2.2.2 Resolve Step Input Mappings
       2.2.3 Call Skill Executor
       2.2.4 Store Step Result
       2.2.5 Propagate Errors
   2.3 Input Mapping (JSON path syntax)

3. Execution Context
   3.1 Lifecycle (creation, mutation, persistence, reference)
   3.2 Read-Only vs Mutable Phases
   3.3 Schema Versioning
   3.4 Large Blob Strategy (references vs inline)

4. Sequence Diagrams
   4.1 Single Skill Execution
   4.2 Workflow Execution (3-step example)
   4.3 Error Scenario (capability failure)
   4.4 Error Scenario (AI provider failure)
```

## Estimated Size

~800 lines

## Diagrams Required

- Skill execution state machine (Mermaid state diagram)
- Workflow execution state machine (Mermaid state diagram)
- Single Skill execution sequence (Mermaid sequence diagram)
- Workflow execution sequence (Mermaid sequence diagram)

## Cross-References

| Target | Relationship |
|--------|-------------|
| 02-System-Architecture | Services referenced here are defined in 02 |
| 05-Core-Services | Per-service interfaces implement these lifecycle phases |
| 06-API-Reference | Entry points that trigger these lifecycles |
| 07-Data-Models | Execution Context schema defined in 07 |
| 08-Contracts | Error envelope, naming conventions used here |
| docs/01-Product/08-Runtime-Architecture.md | Upstream source — this document adds state machines and phase boundaries |
| docs/ADR/0005 | Skill Executor as central orchestrator |
| docs/ADR/0006 | Workflow Runner reuses Skill Executor |
| docs/ADR/0011 | Execution Context object |

## Document Boundary Verification

This document defines the HOW of execution (state sequence, phase transitions, error handling). It does NOT define WHAT the Skill Executor interface looks like (05) or WHERE the execution starts (06 API). Clear boundary: lifecycle vs interface vs entry point.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
