# Deferred Decisions

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Product Scope (05), Future Research Topics (19)

---

This document records decisions that were intentionally deferred during Product Discovery. Each entry explains what was proposed, why it was deferred, and what would trigger revisiting.

## DD-001: Confidence-Based Autonomy Threshold

**Proposal:** Allow HiveOS to automatically adopt patterns above a certain confidence threshold without human approval.

**Deferred to:** V2+ (Learning Architecture phase)

**Rationale:** In V1, humans must validate every recommendation. Autonomous adoption introduces risks around false positives, trust erosion, and audit complexity that are inappropriate for an MVP.

**Trigger for revisit:** Pattern detection is reliable enough in practice (measured precision > 95%). Customer demand for reduced manual review.

**Reference:** ADC-001, ADR-0016

## DD-002: Multiple Domain Pack Coexistence

**Proposal:** Allow installing and using multiple Domain Packs simultaneously in one Business.

**Deferred to:** V2+ (after single-pack V1)

**Rationale:** V1 ships with one Domain Pack. Cross-pack concerns (ontology merging, conflict resolution, dependency management) are not needed until the second pack exists.

**Trigger for revisit:** Second Domain Pack enters development.

## DD-003: Visual Workflow Builder (Playground Canvas)

**Proposal:** Drag-and-drop visual flow builder for composing custom Workflows.

**Deferred to:** V2+

**Rationale:** V1 customers run pre-built Workflow Templates. The visual builder is months of frontend engineering that serves zero V1 customers. The Playground in V1 is a developer debug console, not a canvas.

**Trigger for revisit:** Customers request custom Workflow composition.

## DD-004: Fine-Grained RBAC

**Proposal:** Role-based access control with resource-level permissions, multiple roles, and audit.

**Deferred to:** V2+

**Rationale:** V1 has one Business with a small team. A simple admin/user boolean suffices. Fine-grained RBAC adds weeks of design, implementation, and testing before any customer needs it.

**Trigger for revisit:** Customer requires departmental access controls or external auditor review.

## DD-005: Separate Prompt Asset Files

**Proposal:** Extract AI prompts from Skill YAML into separate files with versioning and localization support.

**Deferred to:** V2+

**Rationale:** V1 has ~5 Skills. Embedded prompts are manageable. Prompt extraction adds file management complexity without proportional benefit.

**Trigger for revisit:** Domain Pack grows beyond 10 Skills. Multi-language prompt support is needed.

## DD-006: Two-Way System Integration

**Proposal:** HiveOS writes results back to ERP, CRM, or accounting software.

**Deferred to:** V2+

**Rationale:** Two-way integration adds API contracts, authentication, error handling, idempotency, and consistency guarantees. V1 focuses on the intelligence layer (read and process), not the execution layer (write back).

**Trigger for revisit:** Customer requires automated posting of processed results to their accounting system.

## DD-007: Cross-Organization Anonymized Learning

**Proposal:** Aggregate patterns across opt-in customer installations for improved pattern detection.

**Deferred to:** Long Term

**Rationale:** Requires multiple HiveOS installations, privacy infrastructure, opt-in consent, and anonymization. Entirely premature for V1.

**Trigger for revisit:** 100+ active HiveOS installations.

## DD-008: Streaming AI Responses

**Proposal:** Stream AI responses token-by-token for real-time UX.

**Deferred to:** V2+

**Rationale:** Adds significant complexity to the AI Provider interface, Execution Context, and UI. V1 processes complete responses. Streaming is a UX enhancement, not a functional requirement.

**Trigger for revisit:** Customer feedback on response time.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
