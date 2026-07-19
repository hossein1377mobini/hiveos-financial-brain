# Open Questions

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Draft  
> **Last Updated:** 2026-07-19  
> **References:** Assumptions (16), Deferred Decisions (18)

---

This document records questions that arose during Product Discovery but were not definitively answered. These are open topics that need resolution in future phases.

## Product Questions

### Q-001: What Is the Pricing Model?
Domain Packs could be sold, licensed, or bundled. The platform could be free with paid Domain Packs, or paid with included Domain Packs. Pricing is not defined yet.

**Depends on:** Business model decisions, market research.

### Q-002: What Is the Target Customer Size?
V1 targets "organizations with existing IT infrastructure." Is this 10-person firms, 50-person firms, or 500-person enterprises? The deployment model, hardware requirements, and support model differ dramatically.

**Depends on:** Customer discovery, market validation.

### Q-003: Who Is the Primary Buyer?
Is the buyer the IT department, the finance director, the CEO, or an external consultant? The buying criteria, decision process, and required proof points differ.

**Depends on:** Sales discovery.

## Technical Questions

### Q-004: What Is the Minimum Hardware Required for Local AI?
Running local models requires specific hardware (RAM, GPU, or NPU). The minimum spec for a reasonable user experience is unknown.

**Depends on:** Testing with target models (Llama 3.1, Qwen 2.5) on target hardware.

### Q-005: How Are Domain Packs Distributed?
If HiveOS authors all Domain Packs, how are they delivered? Separate download? Bundled with installer? In-app purchase? Pulled from a registry?

**Depends on:** Domain Pack distribution strategy (Phase 2+).

## Architectural Questions

### Q-006: What Happens When Execution History Exceeds Storage Capacity?
If a customer runs 10,000 Skills per day, the execution history grows rapidly. What is the retention policy? Are there export/archive mechanisms?

**Depends on:** Usage patterns observed in V1.

### Q-007: How Do Custom Skills (V2+) Interact with Domain Pack Updates?
If a customer created a Custom Skill that depends on a Domain Pack Skill, and the Domain Pack updates with breaking changes — what happens?

**Depends on:** Domain Pack versioning strategy (V2+).

## Open Decisions Awaiting Input

### Q-008: Should the Dashboard Be a Separate Service or Embedded?
The Dashboard UI could be a separate frontend service (like the Playground React app) or embedded as simple HTML pages served by the Core API Gateway.

**Decision deferred to:** Phase 1 — Core Architecture.

### Q-009: Should the Configuration Service Be a File or a Database?
Config could live in a YAML file (like current config.yaml) or in the database. File is simpler for single-user, database enables multi-user admin via Dashboard.

**Decision deferred to:** Phase 1 — Core Architecture.

---

## Question Lifecycle

When an open question is resolved:
1. Record the answer in the relevant document.
2. Move the question to Deferred Decisions (if deferred) or close it.
3. Reference the ADR that resolved it.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
