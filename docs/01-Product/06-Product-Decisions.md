# Product Decisions

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Each decision references the relevant ADR and affected documents

---

## Decision Register

Every significant product decision is recorded here. Decisions are numbered and linked to their corresponding Architecture Decision Record (ADR) for full rationale.

### PD-01: Domain Packs Are Declarative, Not Executable
- **Decision:** Domain Packs contain only declarative content (YAML, Markdown, structured data). No executable code of any kind.
- **Rationale:** Prevents supply chain attacks, keeps packs portable, enables domain expert authorship without engineering skills.
- **ADR:** ADR-0001
- **Status:** Approved

### PD-02: V1 Ships Productivity, Not Learning
- **Decision:** Pattern detection, recommendation engine, and learning from rejection are V2. V1 collects execution history only.
- **Rationale:** Learning requires usage data that doesn't exist at launch. Building pattern detection without data is premature optimization.
- **ADR:** ADR-0002
- **Status:** Approved

### PD-03: AI Provider Must Be Abstract
- **Decision:** The Core defines an AI Provider interface. All Skill execution communicates through this interface. No direct coupling to any vendor.
- **Rationale:** Protects against vendor lock-in, enables on-premise (local models) and cloud (optional) from the same architecture.
- **ADR:** ADR-0003
- **Status:** Approved

### PD-04: Capabilities Are a Separate Layer Between Knowledge and Skills
- **Decision:** Skills declare required capabilities by ID. The Core owns capability implementations. Skills do not implement system functions.
- **Rationale:** Prevents Skills from reinventing common functions, keeps Skills focused on domain logic, enables capability reuse across domains.
- **ADR:** ADR-0004
- **Status:** Approved

### PD-05: Skill Executor Is the Central Orchestrator
- **Decision:** Every Skill execution goes through the Skill Executor. It loads definitions, orchestrates capabilities, communicates with AI Provider, validates outputs, and records history.
- **Rationale:** Single execution path simplifies debugging, enables consistent audit, prevents execution logic from scattering across components.
- **ADR:** ADR-0005
- **Status:** Approved

### PD-06: Workflow Runner Reuses Skill Executor
- **Decision:** The Workflow Runner does not implement its own Skill execution logic. It iterates through Workflow steps and calls the Skill Executor for each one.
- **Rationale:** Eliminates dual-execution problem, ensures consistent execution behavior, reduces code surface.
- **ADR:** ADR-0006
- **Status:** Approved

### PD-07: Single Knowledge Index with Source Tagging
- **Decision:** Domain Knowledge and Organization Knowledge live in one searchable index. Documents are tagged with source type (domain: or org:).
- **Rationale:** Eliminates complex merge infrastructure for V1 while preserving separation. Source tags enable future split if needed.
- **ADR:** ADR-0007
- **Status:** Approved

### PD-08: On-Premise Default Deployment
- **Decision:** HiveOS deploys on customer infrastructure by default. Cloud AI provider is optional and configurable.
- **Rationale:** Data sovereignty is non-negotiable. Enterprise customers require on-premise for regulated data.
- **ADR:** ADR-0008
- **Status:** Approved

### PD-09: Prompts Embedded in V1 Skills
- **Decision:** Skill definitions include prompt instructions inline. Separate prompt asset files are V2.
- **Rationale:** V1 has ~5 Skills. Extracting prompts adds file management complexity for no benefit at this scale. Refactoring 5 files when needed is an afternoon's work.
- **ADR:** ADR-0009
- **Status:** Approved

### PD-10: Flat Domain Pack Directory Structure
- **Decision:** V1 Domain Packs use a flat directory structure (max 1 level deep). Nested directories can be introduced later.
- **Rationale:** Simple parser, easy to understand, easy to author. Nesting can be added backward-compatibly.
- **ADR:** ADR-0010
- **Status:** Approved

### PD-11: Execution Context Object
- **Decision:** Every Skill and Workflow execution creates an Execution Context object that carries all state through the lifecycle.
- **Rationale:** Single source of truth per execution, enables complete audit trail, simplifies debugging, feeds Execution History.
- **ADR:** ADR-0011
- **Status:** Approved

### PD-12: No Executable Code in Domain Packs
- **Decision:** (Same as PD-01, reinforced) Domain Packs contain zero executable code. Only declarative definitions.
- **Rationale:** Security, portability, domain expert authorship.
- **ADR:** ADR-0012
- **Status:** Approved

### PD-13: Simplified RBAC in V1
- **Decision:** V1 RBAC is a single boolean: admin or user. No fine-grained permissions, roles, or resource-level access control.
- **Rationale:** V1 has one Business with a small team. RBAC complexity adds weeks of design, implementation, and testing before any customer needs it.
- **ADR:** ADR-0013
- **Status:** Approved

### PD-14: No Visual Workflow Builder in V1
- **Decision:** V1 Playground is a developer debug console (run Skill, inspect results), not a visual drag-drop canvas.
- **Rationale:** Visual builder is months of React engineering. V1 customers run pre-built templates. Custom workflow authoring is V2.
- **ADR:** ADR-0014
- **Status:** Approved

### PD-15: Human Ownership of Business Truth
- **Decision:** The system never changes business rules autonomously. Every recommendation requires human validation.
- **Rationale:** Core philosophical principle. Trust is earned, not assumed. Disagreement is a learning mechanism.
- **ADR:** ADR-0015
- **Status:** Approved

### PD-16: No Two-Way System Integration in V1
- **Decision:** V1 HiveOS reads from external systems (via file ingestion). It does not write back to ERP, CRM, or accounting software.
- **Rationale:** Two-way integration adds API contracts, auth, error handling, and consistency guarantees. V1 focuses on the intelligence layer, not the write-back layer.
- **Status:** Approved (no ADR required — covered by V1 scope)

---

## Decision Status Meanings

| Status | Meaning |
|--------|---------|
| **Approved** | Decision is final for the current scope. Can be revisited via ADR. |
| **Deferred** | Decision postponed to a later phase. Original proposal documented. |
| **Rejected** | Decision was proposed and explicitly rejected with rationale. |
| **Superseded** | A later decision overruled this one. Reference to superseding decision. |

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
