# ADR-0014: No Visual Workflow Builder in V1

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

A visual drag-and-drop workflow builder (canvas, node palette, connection drawing, property panels) is a compelling feature. However, V1 customers run pre-built Workflow Templates from Domain Packs — they do not create custom workflows.

## Decision

V1 does not include a visual workflow builder. The V1 "Playground" is a developer debug console for running individual Skills, inspecting prompts, viewing retrieved knowledge, and examining AI responses. The visual builder is deferred to V2.

## Rationale

- V1 customers use pre-built Workflow Templates. There is no customer need for custom workflow composition in V1.
- A visual workflow builder is months of frontend engineering (React Flow, node types, drag-drop, property editing, validation). This effort serves zero V1 customers.
- The debug console (Skill Test Console) serves an immediate, essential need: Domain Pack developers must test and debug Skills during authoring.

## Consequences

- Positive: V1 engineering focuses on Core platform, not UI features.
- Positive: The Playground debug console improves Domain Pack quality (developers can test Skills before release).
- Negative: V1 cannot demonstrate "visual workflow building" in demos or sales calls.
- Negative: The debug console is a developer tool, not a customer-facing feature for non-technical users.

## References

- Product Decisions: PD-14
- Product Scope: V1 section (Playground), V2 section
- Deferred Decisions: DD-003
- Product Principles P4 (Practical Value), P10 (Buildability)
