# 04 — Domain Pack Specification

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Upstream Sources:** `docs/01-Product/09-Domain-Pack-Specification.md`, `docs/ADR/0001`, `0010`, `0012`  
> **Dependencies:** 01-System-Vision (for scope context)  
> **Priority:** 3  

---

## Purpose

Complete technical reference for the Domain Pack format. A pack author (HiveOS domain expert or future third-party) reads this document to create a valid Domain Pack. An implementer reads this to build the Domain Pack Manager, Skill Loader, and Workflow Loader.

## Scope

**In:** `domain.yaml` manifest schema (JSON Schema), directory structure with file type requirements, knowledge file format requirements, Skill file format reference (imports from 04-referenced Skill spec), Workflow file format reference, install/update/enable/disable/remove lifecycle with state transitions, portability guarantees, V1 constraints table, extension points for V2.

**Out:** Skill execution logic (05-Core-Services), Workflow execution logic (05-Core-Services), product-level definition of what a Domain Pack is (01-Product/09).

## Table of Contents

```
1. Format Overview
   1.1 Directory Structure (flat, V1)
   1.2 File Types and MIME Types
   1.3 Naming Conventions (qualified IDs)

2. domain.yaml Manifest
   2.1 Schema (JSON Schema)
   2.2 Required Fields
   2.3 Optional Fields
   2.4 Validation Rules
   2.5 Example

3. Knowledge Directory
   3.1 Accepted Formats (Markdown only in V1)
   3.2 Frontmatter Requirements
   3.3 Knowledge Tagging Convention
   3.4 Source Tagging (domain: prefix)
   3.5 File Organization

4. Skills Directory
   4.1 One YAML File per Skill
   4.2 Skill Schema (JSON Schema)
   4.3 Embedded Prompt Format (V1)
   4.4 Required Capabilities Declaration
   4.5 Knowledge Requirements Declaration
   4.6 Input Schema (JSON Schema subset)
   4.7 Output Schema (JSON Schema subset)
   4.8 Model Configuration Block
   4.9 Complete Example

5. Workflows Directory
   5.1 One YAML File per Workflow Template
   5.2 Workflow Schema (JSON Schema)
   5.3 Step Definitions
   5.4 Input Mapping Syntax
   5.5 Output Mapping
   5.6 Error Handling (on_error — V1: fail only)
   5.7 Complete Example

6. Domain Pack Lifecycle
   6.1 Install
   6.2 Update
   6.3 Enable
   6.4 Disable
   6.5 Remove
   6.6 State Machine
   6.7 Storage Layout

7. V1 Constraints
   7.1 Single Pack Per Installation
   7.2 Flat Directory (no nesting)
   7.3 No Dependencies Between Packs
   7.4 No Capabilities Declaration in Manifest
   7.5 Read-Only After Installation
   7.6 Portability Guarantees

8. V2 Extension Points
   8.1 Nested Directories
   8.2 Pack Dependencies
   8.3 Capabilities Declaration
   8.4 Prompt Asset Files
   8.5 Multiple Languages
   8.6 Checksums and Signing
```

## Estimated Size

~700 lines

## Diagrams Required

- Directory structure tree diagram (ASCII)
- Pack lifecycle state machine (Mermaid state diagram)

## Cross-References

| Target | Relationship |
|--------|-------------|
| 01-System-Vision | Glossary terms (Skill, Workflow, Knowledge) used here |
| 03-Runtime-Execution | Lifecycle phases reference this format |
| 05-Core-Services | Domain Pack Manager implements these lifecycle operations |
| 07-Data-Models | Skill/Workflow/Knowledge schemas formally defined in 07 |
| 13-Developer-Guide | Developer tutorial for creating a Domain Pack references this |
| docs/01-Product/09-Domain-Pack-Specification.md | Product-level definition — this document adds schema and rules |
| docs/ADR/0001 | Domain Packs are declarative |
| docs/ADR/0009 | Embedded prompts in V1 |
| docs/ADR/0010 | Flat directory structure |
| docs/ADR/0012 | No executable code in packs |

## Document Boundary Verification

This document defines the STATIC format of Domain Packs (what files, what schema). It does NOT define how packs are executed (03), how the Domain Pack Manager implements lifecycle operations (05), or how packs are distributed (11-Deployment). Clear boundary: format vs runtime vs distribution.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
