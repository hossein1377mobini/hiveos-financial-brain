# 12 — ADR Index

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Upstream Sources:** `docs/ADR/` (all 16 ADRs)  
> **Dependencies:** None (reference document)  
> **Priority:** 7  

---

## Purpose

Referenced index of all Architecture Decision Records with component mapping. Links each ADR to the technical components it constrains. An engineer making changes to a component checks this index to understand which decisions must not be violated.

## Scope

**In:** ADR table with columns (number, title, status, components affected, constraint type), component-to-ADR reverse map, summary of each ADR in one line.

**Out:** Full ADR text lives in `docs/ADR/` — this document summarizes and links.

## Table of Contents

```
1. ADR Index Table
   Columns: #, Title, Status, Components Affected, Constraint Type

2. Component-to-ADR Reverse Map
   2.1 Skill Executor → ADR-0005
   2.2 Workflow Runner → ADR-0006
   2.3 Knowledge Service → ADR-0007
   2.4 Capability Service → ADR-0004
   2.5 AI Provider Service → ADR-0003
   2.6 Execution History → ADR-0002, 0011
   2.7 Domain Pack Manager → ADR-0001, 0009, 0010, 0012
   2.8 Core API Gateway → ADR-0013
   2.9 Security → ADR-0013, 0015

3. ADR Status Summary
   Approved: 15 | Deferred: 1 | Superseded: 0
```

## Estimated Size

~200 lines

## Cross-References

| Target | Relationship |
|--------|-------------|
| docs/ADR/ | Full ADR text (upstream source) |
| docs/02-Architecture/02-System-Architecture.md | Components listed in architecture map |
| docs/02-Architecture/05-Core-Services.md | ADR constraints on each service |
