# Technical Architecture — Index

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outlines)  
> **Last Updated:** 2026-07-19  
> **Upstream Sources:** `docs/01-Product/` (frozen), `docs/ADR/` (frozen)  
> **Supersedes:** Old `docs/02-Architecture/` (pre-discovery content)

---

## Purpose

This directory is the complete technical reference for HiveOS. Every document here derives from the frozen product definitions in `docs/01-Product/` and the architecture decisions in `docs/ADR/`. A developer implementing HiveOS reads these documents — they contain all contracts, schemas, service boundaries, and rules necessary to build the system.

## Document List

| # | File | Purpose | Dependencies | Priority |
|---|------|---------|--------------|----------|
| 01 | 01-System-Vision.md | Distilled product vision for engineers | 01-Product/ | 1 |
| 02 | 02-System-Architecture.md | C4-level component diagram, service map | 01 | 2 |
| 03 | 03-Runtime-Execution.md | Skill/Workflow execution lifecycle | 02 | 3 |
| 04 | 04-Domain-Pack-Specification.md | Pack format, schema, lifecycle | 01-Product/09 | 3 |
| 05 | 05-Core-Services.md | Every Core service: boundaries, interfaces, state | 02, 03 | 4 |
| 06 | 06-API-Reference.md | External HTTP contracts | 05, 07 | 5 |
| 07 | 07-Data-Models.md | All shared schemas | 05 | 5 |
| 08 | 08-Contracts.md | Service-to-service conventions | 07 | 5 |
| 09 | 09-Configuration.md | Config keys, defaults, storage | 05 | 6 |
| 10 | 10-Security.md | Auth, RBAC, data isolation | 05 | 6 |
| 11 | 11-Deployment.md | On-premise deployment guide | 09, 10 | 7 |
| 12 | 12-ADR-Index.md | ADR reference with component mapping | docs/ADR/ | 7 |
| 13 | 13-Developer-Guide.md | Setup, build, test, contribute | All | 8 |
| 14 | 14-Testing.md | Test strategy, levels, infrastructure | 05, 13 | 8 |
| 15 | 15-Future-Roadmap.md | V2+ deferred features reference | 01-Product/ | 9 |

## Relationship to 01-Product/

| Aspect | docs/01-Product/ (Product Reference) | docs/02-Architecture/ (Technical Reference) |
|--------|--------------------------------------|---------------------------------------------|
| Audience | Product managers, architects, domain experts | Developers, testers, devops |
| Content | What and Why | How and Where |
| Stability | Frozen after Product Discovery | Evolves with implementation |
| Format | Prose, principles, scope | Schemas, interfaces, contracts |
| Decisions | Product Decisions (PD-xx) | ADRs + technical specifications |

## ADR Reference Map

Every document references specific ADRs. Full list:

| ADR | Title | Affects Documents |
|-----|-------|-------------------|
| 0001 | Declarative Domain Packs | 04-Domain-Pack |
| 0002 | Execution Over Learning V1 | 03-Runtime, 05-Core (History Svc) |
| 0003 | AI Provider Abstraction | 05-Core (AI Provider Svc) |
| 0004 | Capability Layer | 05-Core (Capability Svc) |
| 0005 | Skill Executor Central Orchestrator | 05-Core (Skill Executor) |
| 0006 | Workflow Runner Reuses Skill Executor | 05-Core (Workflow Runner) |
| 0007 | Single Knowledge Index w/ Tagging | 05-Core (Knowledge Svc) |
| 0008 | On-Premise Default | 11-Deployment |
| 0009 | Embedded Prompts V1 | 04-Domain-Pack (Skill format) |
| 0010 | Flat Directory Structure | 04-Domain-Pack (dir structure) |
| 0011 | Execution Context Object | 03-Runtime, 07-Data-Models |
| 0012 | No Code in Domain Packs | 04-Domain-Pack |
| 0013 | Simplified RBAC V1 | 10-Security |
| 0014 | No Visual Workflow Builder V1 | All V1 scope references |
| 0015 | Human Ownership of Truth | 10-Security |
| 0016 | Confidence Autonomy Threshold | 15-Future-Roadmap |

## Documentation Traceability Matrix

See `docs/02-Architecture/XX-Traceability-Matrix.md` — generated at the end of Phase 2 after all documents are complete.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
