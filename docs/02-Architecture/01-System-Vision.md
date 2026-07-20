# 01 — System Vision

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Upstream Sources:** `docs/01-Product/01-Product-Bible.md`, `02-Product-Principles.md`, `03-Product-Glossary.md`, `04-Product-Vision.md`, `05-Product-Scope.md`  
> **Dependencies:** None (first document in dependency order)  
> **Priority:** 1 — first document a new engineer reads  

---

## Purpose

Distilled extract of the Product Bible, Vision, Principles, Glossary, and Scope for technical readers. A new engineer reads this first to understand what HiveOS is, why it exists, and what it must deliver — without reading 20 product documents. Does NOT replace the product docs; provides essential context for all technical work.

## Scope

**In:** Product identity, five pillars (Knowledge, Skills, Workflows, Learning, Brain), target audience, V1 boundaries (what ships vs what defers), product principles (10), glossary of all defined terms.

**Out:** Marketing language, speculative future features, detailed technical architecture, implementation instructions.

## Table of Contents

```
1. Why HiveOS Exists
   1.1 The Problem
   1.2 The Solution
   1.3 Elevator Pitch
   1.4 Why "OS"

2. Five Pillars
   2.1 Knowledge — What the Business Knows
   2.2 Skills — What the System Can Do
   2.3 Workflows — How Work Gets Done
   2.4 Learning — How the System Improves (V2+)
   2.5 Brain — The Merged Intelligence

3. Core Philosophy
   3.1 Glass Box
   3.2 Human-in-the-Loop
   3.3 Domain-Native
   3.4 Declarative over Imperative
   3.5 Self-Learning (V2+)
   3.6 Portable by Default
   3.7 Observable
   3.8 Resilient

4. Product Principles (10)
   P1 Simplicity · P2 Human Ownership · P3 Modularity
   P4 Practical Value · P5 Augment First · P6 On-Premise First
   P7 Extensibility · P8 Declarative · P9 Data Sovereignty
   P10 Buildability

5. Glossary (definitions)
   Business · Domain Pack · Organization Knowledge · Skill
   Workflow · Pattern · Capability · Core · Organization Brain
   Execution Context · Execution History · AI Provider
   Human Ownership · Playground · Workspace

6. V1 Scope Summary
   6.1 What Ships in V1
   6.2 Explicitly NOT in V1
   6.3 Design Constraints (productivity over learning, single Domain Pack,
        flat structure, embedded prompts, simplified RBAC, sequential Workflows)
```

## Estimated Size

~600 lines

## Cross-References

| Target | Relationship |
|--------|-------------|
| docs/01-Product/01-Product-Bible.md | Upstream source for identity, philosophy |
| docs/01-Product/04-Product-Vision.md | Upstream source for pillars, pitch |
| docs/01-Product/02-Product-Principles.md | Upstream source for principles |
| docs/01-Product/03-Product-Glossary.md | Upstream source for glossary |
| docs/01-Product/05-Product-Scope.md | Upstream source for V1 boundaries |
| docs/02-Architecture/02-System-Architecture.md | Next document in dependency chain |

## Document Boundary Verification

This document does not overlap with 02-System-Architecture (which covers components and their relationships). 01-System-Vision is the "why" context; 02-System-Architecture is the "what" map. Clear boundary: principles and scope belong here, components and communication belong in 02.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
