# 02 — System Architecture

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Upstream Sources:** `docs/01-Product/07-Architecture-Principles.md`, `docs/01-Product/08-Runtime-Architecture.md`, all ADRs  
> **Dependencies:** 01-System-Vision  
> **Priority:** 2  

---

## Purpose

High-level component architecture of HiveOS. Shows every Core service, their boundaries, communication paths, data stores, and deployment unit. This is the "big picture" diagram that all other technical documents decompose. A developer reads this to understand what exists, where it lives, and how components communicate.

## Scope

**In:** C4-level container diagram (System Context → Containers → Components), service responsibility table, data store definitions, communication protocols (sync HTTP, file system), deployment boundary, component dependency graph.

**Out:** Runtime execution details (delegated to 03), per-service interface definitions (delegated to 05), API endpoint contracts (delegated to 06).

## Architecture Principles (from Product)

Referenced, not restated: A1 (Single Execution Path), A2 (Service-Oriented), A3 (Declarative Boundaries), A4 (Immutable Core), A5 (Local-Only Default), A6 (Observable), A7 (Fail Explicitly), A8 (Configuration over Hardcoding), A9 (Interface Stability), A10 (Storage Separation).

## Table of Contents

```
1. System Context Diagram
   1.1 Actors (User, Domain Pack Author, Administrator)
   1.2 External Systems (Local AI, Cloud AI, File System)
   1.3 HiveOS System Boundary

2. Container Diagram
   2.1 Core Services
   2.2 Dashboard (Web UI)
   2.3 Persistent Storage
   2.4 Communication Paths (HTTP sync, file I/O)

3. Core Services — Responsibility Table
   3.1 Core API Gateway
   3.2 Skill Executor (+ sub-phases: Loader, InputValidator,
        ContextBuilder, PromptCompiler, AIInvoker, OutputValidator,
        ExecutionRecorder)
   3.3 Workflow Runner
   3.4 Knowledge Service
   3.5 Capability Service (+ Core Capabilities list)
   3.6 AI Provider Service (+ adapters)
   3.7 Execution History Service
   3.8 Configuration Service
   3.9 Domain Pack Manager

4. Data Stores
   4.1 Domain Pack Storage (read-only files)
   4.2 Organization Knowledge Storage (mutable files + index)
   4.3 Execution History Database (append-only)
   4.4 Configuration Store (config file)

5. Component Dependency Graph
   (which services call which, direction of dependency)

6. Deployment Boundary
   6.1 Single Process vs Multi-Process
   6.2 On-Premise Packaging
   6.3 Network Ports
```

## Estimated Size

~500 lines

## Diagrams Required

- C4 System Context diagram (ASCII or Mermaid)
- C4 Container diagram showing all Core services and their connections
- Component dependency graph (directed, showing caller → callee)

## Cross-References

| Target | Relationship |
|--------|-------------|
| 01-System-Vision | Provides principles and scope that define these components |
| 03-Runtime-Execution | Decomposes the execution flow through these components |
| 05-Core-Services | Per-service interface definitions (depends on this component map) |
| docs/01-Product/07-Architecture-Principles.md | Architecture principles are constraints on this design |
| All ADRs | Every ADR constrains one or more components listed here |

## Document Boundary Verification

This document defines WHAT services exist and HOW they connect. It does NOT define execution order (delegated to 03), service interfaces (delegated to 05), or API contracts (delegated to 06). No overlap: component existence and communication paths are distinct from lifecycle, interfaces, and protocols.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
