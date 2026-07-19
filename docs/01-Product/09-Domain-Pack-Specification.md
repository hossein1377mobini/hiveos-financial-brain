# Domain Pack Specification

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Product Bible (01), Skill Specification (13), Workflow Specification (14), ADR-0001, ADR-0010, ADR-0012

---

## 1. Purpose

A Domain Pack encapsulates and delivers industry-specific expertise to a HiveOS Business. Its primary purpose is to provide immediate, out-of-the-box value by provisioning pre-built foundational knowledge, reusable AI Skills, and ready-to-use Workflow Templates for a specific business domain.

Domain Packs are the mechanism through which HiveOS delivers domain expertise. Customers install Domain Packs — they do not create them.

## 2. Responsibilities of a Domain Pack

- Define structured knowledge: ontology, concepts, terminology, rules, and best practices.
- Provide pre-built AI Skills that perform common domain tasks.
- Offer Workflow Templates that orchestrate Skills for typical business outcomes.
- Declare metadata: unique identifier, version, name, description, minimum Core version, author.

## 3. What a Domain Pack Is NOT

- A Domain Pack does NOT contain executable code.
- A Domain Pack does NOT modify Core behavior.
- A Domain Pack does NOT depend on other Domain Packs (in V1).
- A Domain Pack does NOT reference external network resources.
- A Domain Pack is NOT a database — it is a directory of files.

## 4. Boundary with HiveOS Core

| Responsibility | Owner |
|----------------|-------|
| Loading and parsing Domain Pack files | Core (Domain Pack Manager) |
| Providing runtime for Skills and Workflows | Core (Skill Executor, Workflow Runner) |
| Managing Knowledge (domain + organization) | Core (Knowledge Service) |
| Executing capabilities (search, file reading, etc.) | Core (Capability Service) |
| Storing execution history | Core (Execution History Service) |
| Providing Dashboard and UI | Core (API Gateway + Dashboard) |
| Defining domain knowledge content | Domain Pack |
| Defining Skill definitions | Domain Pack |
| Defining Workflow Template definitions | Domain Pack |
| Declaring metadata and version | Domain Pack |

## 5. Directory Structure (V1 — Flat)

```
accounting/                       # Directory named after domain pack ID
├── domain.yaml                   # REQUIRED: Manifest and metadata
├── knowledge/                    # REQUIRED: Domain knowledge documents
│   ├── 01-accounting-principles.md
│   ├── 02-tax-rules.md
│   └── 03-chart-of-accounts.md
├── skills/                       # REQUIRED: Skill definitions (one YAML per Skill)
│   ├── validate-invoice.yaml
│   ├── categorize-expense.yaml
│   ├── check-tax-compliance.yaml
│   ├── generate-financial-report.yaml
│   └── summarize-policy.yaml
├── workflows/                    # OPTIONAL: Workflow Template definitions
│   ├── invoice-processing.yaml
│   └── month-end-close.yaml
└── icon.png                      # OPTIONAL: Single icon at root
```

**Design rules:**
- Maximum one level of directory nesting.
- No nested `assets/` directories — one icon at root is sufficient for V1.
- Knowledge files are flat Markdown with no subdirectories.
- Ontology is implicit in the structure and content of knowledge files. Formal ontology YAML is V2+.
- Prompt instructions are embedded inside Skill YAML files, not separate assets.

## 6. Domain Manifest (domain.yaml)

```yaml
id: accounting                          # Globally unique identifier
version: 1.0.0                          # Semver
name: Accounting Domain Pack
description: >
  Pre-built knowledge, skills, and workflows for Iranian accounting.
  Covers financial recording, tax compliance, expense categorization,
  invoice validation, and financial reporting.
min_core_version: 1.0.0                 # Minimum HiveOS Core version required
author:
  name: HiveOS
  url: https://hiveos.com
skills:                                 # List of Skill IDs in this pack
  - id: validate-invoice
  - id: categorize-expense
  - id: check-tax-compliance
  - id: generate-financial-report
  - id: summarize-policy
workflows:                              # List of Workflow Template IDs in this pack
  - id: invoice-processing
  - id: month-end-close
```

**Note:** `capabilities`, `dependencies`, and `permissions` fields are intentionally omitted for V1. They will be added when multiple Domain Packs coexist and cross-pack resolution is needed.

## 7. Domain Pack Lifecycle

| Operation | Behavior |
|-----------|----------|
| **Install** | Pack is unpacked into `domains/<id>/`. Core discovers `domain.yaml`, validates structure, registers Knowledge/Skills/Workflows. |
| **Update** | New version replaces old pack directory. Core validates compatibility (`min_core_version`). Organization Knowledge is unaffected. Custom Skills/Workflows (V2+) are unaffected. |
| **Enable** | Pack's Knowledge, Skills, and Workflows become available to the Organization Brain. |
| **Disable** | Pack's content becomes unavailable. No data loss. Organization Knowledge unaffected. |
| **Remove** | Pack directory deleted. Organization Knowledge and custom content unaffected. |

## 8. Domain Pack Content Ownership

| Content | Owner | Mutable? |
|---------|-------|----------|
| Domain Pack files (knowledge/, skills/, workflows/) | HiveOS (pack author) | Read-only after installation |
| Organization Knowledge (customer documents, observed patterns) | Customer | Mutable |
| Custom Skills (V2+) | Customer | Mutable |
| Custom Workflows (V2+) | Customer | Mutable |
| Execution History | System (on behalf of customer) | Append-only |

The Core never writes to Domain Pack files. All Organization-Owned content is stored separately.

## 9. Portability

A Domain Pack is a directory. It can be copied from one HiveOS instance to another and installed. No registry, no database entries, no compilation, no environment-specific configuration required.

Portability constraints:
- All internal references are relative to the pack root.
- No hardcoded absolute paths.
- No system-level dependencies.
- No network resource references.

## 10. Multiple Domain Pack Coexistence (V2+)

V1 supports exactly one Domain Pack per installation. When V2 adds multi-pack support:

- Each pack has a globally unique `id` for namespacing.
- Packs are loosely coupled — no direct dependencies between packs.
- The Organization Brain merges ontologies at query time.
- Conflict resolution rules are configurable by the Business administrator.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
