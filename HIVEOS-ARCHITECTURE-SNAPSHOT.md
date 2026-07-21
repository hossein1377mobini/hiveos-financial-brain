# HiveOS — Architecture & Product Memory Snapshot

> **Generated:** 2026-07-20
> **Source Documents:** `docs/01-Product/` (20 files), `docs/ADR/` (16 records), `docs/02-Architecture/` (13 outlines)
> **Status:** Phase 0 (Product Discovery) complete. Phase 1 (Core Architecture) outlines written, content pending.

---

# 1. Product Vision

## What HiveOS Is

HiveOS is an **Organizational Intelligence Platform** — an on-premise intelligence layer that sits above existing business systems. It observes how work happens, preserves organizational experience, and grows smarter as the organization grows.

Not a chatbot. Not a workflow builder (though it contains one). Not a knowledge base (though it contains one). Does not replace ERP, CRM, or accounting software.

The one-sentence core: *HiveOS is an organizational intelligence platform that sits above existing business systems, observes how work happens, preserves experience, and grows smarter as the organization grows.*

## Long-Term Vision

HiveOS becomes the central place where:
- Business knowledge is organized and searchable
- AI agents understand the company's context
- Workflows are created and automated
- Organizational experience is preserved instead of being lost when employees leave
- New employees become productive faster
- The organization continuously improves through accumulated knowledge and feedback

Five pillars define the vision:
1. **Knowledge** — What the business knows (searchable workspace in V1, living knowledge long-term)
2. **Skills** — What the system can do (pre-built in V1, custom-authored in V2+)
3. **Workflows** — How work gets done (pre-built templates in V1, complex branching in long-term)
4. **Learning** — How the system improves (execution history only in V1, full pattern detection in V2)
5. **Brain** — The merged intelligence (search + execute in V1, interactive visualization in long-term)

## Current V1 Scope

**Tagline:** "Your organization's knowledge, made computable from day one."

V1 is a **productivity platform**. Customers install HiveOS, connect their knowledge, and immediately search across domain expertise and run pre-built skills.

### Ships in V1:
- On-premise installation (single Business per installation)
- Admin user account (boolean RBAC — no fine-grained permissions)
- Domain Pack Manager (install, enable, disable, remove)
- Knowledge Service (unified search index with source tagging: `domain:` / `org:`)
- Organization Knowledge ingestion (PDF + text files from directory)
- Skill Executor (load → knowledge → capabilities → AI → validate → record)
- AI Provider interface with local model adapter (default) + cloud adapter (configurable)
- Capability Service with 4 Core Capabilities: KnowledgeSearch, FileReader, WebAccess, Calculator
- Execution History Service (immutable audit of every execution)
- Workflow Runner (sequential Skill pipeline only)
- Configuration Service
- Core API Gateway (HTTP/WebSocket)
- Dashboard: Searchable Knowledge Workspace, Skill invocation, Workflow Template invocation, Execution History log view, Playground (debug console), Domain Pack management UI
- **Accounting Domain Pack**: 5 core Skills, 2 Workflow Templates, 20-30 knowledge documents

### Explicitly NOT in V1:
- Pattern detection and recommendation engine
- Custom Skill authoring by end-users
- Custom Workflow builder (visual or declarative)
- Learning from rejection
- Multiple Domain Pack coexistence and cross-pack orchestration
- Fine-grained RBAC
- Visual Playground (drag-drop flow builder)
- System connectors to ERP/CRM/accounting APIs
- Multiple Businesses per installation
- Enterprise SSO / LDAP
- Prompts as separate assets (embedded in Skill YAML)
- Ontology merger and cross-pack dependency resolution
- Two-way system integrations (write-back to external systems)
- Full autonomy — every action requires explicit user request

## What Is Intentionally Deferred

See full details in Section 9 (Deferred Features) and `docs/01-Product/18-Deferred-Decisions.md`.

Key deferrals: learning (V2), visual builder (V2), multi-pack (V2), fine-grained RBAC (V2), streaming AI (V2), two-way integrations (V2), cross-org learning (Long Term), confidence-based autonomy (V2+).

---

# 2. Core Philosophy

## Product Principles (ordered by priority)

| Priority | Principle | Tagline |
|----------|-----------|---------|
| P1 | **Simplicity over Completeness** | Build what is needed now. A working simple system > an unfinished comprehensive one. |
| P2 | **Human Ownership of Business Truth** | HiveOS never owns truth. Humans do. The system observes, explains, recommends, learns. Never silently changes rules. |
| P3 | **Modularity over Coupling** | Every component: single responsibility, clear interfaces. No internal implementation dependencies. |
| P4 | **Practical Business Value over Academic Elegance** | Every feature must deliver measurable value. Elegance that doesn't serve a customer need is waste. |
| P5 | **AI Should Augment Humans Before Replacing Them** | Default: assistance, not automation. Full autonomy is earned through trust. |
| P6 | **On-Premise First** | Customer data belongs to customer. HiveOS works fully on-premise. Cloud is optional. |
| P7 | **Extensibility over Specialization** | Platform extends through defined interfaces, not by forking or patching Core. |
| P8 | **Declarative over Imperative** | Define *what*, not *how*. Domain Packs, Skills, Workflows are declarative. |
| P9 | **Data Sovereignty** | Customer knowledge always belongs to customer. HiveOS connects to data; data not forced to HiveOS. |
| P10 | **Buildability by a Small Team** | Everything buildable by 2-3 engineers in 6-9 months for V1. |

### Principle Conflict Resolution Precedence:
P1 → P6 → P2 → P4 → P8 → P3 → P5 → P7 → P10 → P9

## Architecture Principles (derived from Product Principles)

| ID | Principle | Rationale |
|----|-----------|-----------|
| A1 | **Single Execution Path** | Every Skill execution goes through the same Skill Executor, regardless of caller. Prevents dual-engine problem. |
| A2 | **Service-Oriented Internal Architecture** | Core services communicate through defined interfaces. No internal implementation coupling. |
| A3 | **Declarative Boundaries** | Core↔Domain Pack boundary is purely declarative (YAML, Markdown). No code crosses the boundary. |
| A4 | **Immutable Core over Plugin Modification** | Extension → Core enhancement, not Domain Pack plugin. Prevents dependency nightmare. |
| A5 | **Local-Only Default** | Default configuration: no external network dependencies. Cloud AI is documented option. |
| A6 | **Observable by Default** | Every execution recorded with full context. Nothing runs without audit trail. |
| A7 | **Fail Explicitly** | When execution fails, return error with full context. No silent failures, no swallowed exceptions. |
| A8 | **Configuration over Hardcoding** | Every settable parameter is config, not code. Configuration Service provides centralized access. |
| A9 | **Interface Stability over Implementation Flexibility** | Once an interface is documented, changing it requires an ADR. Implementation can change freely behind it. |
| A10 | **Storage Separation** | Domain Pack content and Organization Knowledge stored separately. Domain Packs read-only. "Merged" view is query-time. |

## Guiding Philosophical Tenets

- **Glass Box** — Every action visible, traceable, explainable
- **Human-in-the-Loop** — Critical decisions need human approval
- **Domain-Native** — Knowledge domains are first-class plugins
- **Self-Learning** — Every execution makes the system smarter (V2+)
- **Portable by Default** — Every flow, domain, and package is portable
- **Observable** — Complete monitoring and audit trail
- **Resilient** — System recovers from failures gracefully

---

# 3. Product Model

## Core Concepts

### HiveOS
The platform itself. An on-premise intelligence layer that sits above existing business systems. Observes behavior, discovers patterns, recommends formalization, preserves organizational experience.

### Business
An independent organizational workspace. The security, knowledge, and operational boundary of HiveOS. In V1: one HiveOS installation = one Business. Departments and teams exist inside as logical groups.

### Organization Brain
The merged intelligence: installed Domain Pack(s) + Organization Knowledge + installed Skills + configured Workflows. Unique per customer. The merge is a **query-time join**, not a persisted union.

### Domain Pack
A pre-built product shipped by HiveOS. Contains shared knowledge, ontology, AI Skills, Workflow Templates for a specific business domain. Customers *install* Domain Packs — they do not author them. Domain Packs are read-only, declarative, and portable. No executable code.

### Domain Knowledge
Knowledge shipped inside a Domain Pack. Universal best-practice for an industry or function. Immutable after installation. Updated via Domain Pack releases.

### Organization Knowledge
Customer-specific knowledge: documents, policies, spreadsheets, databases, observed behavior patterns. Lives on customer infrastructure. Owned by the customer. Grows continuously.

### Knowledge Service
Core platform service that indexes, stores, and searches both Domain Knowledge and Organization Knowledge in a **unified index** with source tagging (`domain:` / `org:`).

### Skill
The smallest reusable business capability. Performs a specific business task using Knowledge. Declarative — defines goal, inputs, outputs, required capabilities, knowledge requirements. No executable code. Two origins: Domain Pack Skills (V1) and Custom Skills (V2+).

### Capability
A reusable system-level function owned by the Core. Examples: KnowledgeSearch, FileReader, WebAccess, Calculator. Execution primitives that Skills depend on. Skills declare what they need; Core provides the implementations.

### Workflow
Orchestration of multiple Skills to achieve a business outcome. Two origins: Domain Pack Workflow Templates (pre-built, V1) and Custom Workflows (built by organization, V2+). V1 Workflows are sequential only — no branching, no parallel execution.

### AI Provider
Abstraction layer for AI model interaction. Core defines an interface. Each provider adapter (local/Ollama, cloud/OpenAI-compatible) implements it. Skill Executor communicates only with the interface.

### Skill Executor
Central orchestrator of a single Skill's lifecycle. Loads Skill definitions, orchestrates Capabilities, interacts with AI Provider, validates outputs, records execution history. Every Skill execution passes through this component.

### Workflow Runner
Executes Workflow Templates by iterating through Skill steps and calling the Skill Executor for each step. Does NOT implement its own Skill execution logic.

### Execution Context
Structured container that flows through a single Skill or Workflow execution. Holds all inputs, outputs, intermediate data, retrieved knowledge, generated prompts, AI responses, errors, timestamps, status. Persisted in full by Execution History Service.

### Execution History
Immutable record of every Skill and Workflow execution. Contains the complete Execution Context. Foundation for V2 learning. Serves V1 debugging and audit.

### Pattern (V2+)
A recurring behavior observed across multiple instances, with supporting evidence and confidence level. A candidate, not truth. Requires human validation.

### Core (HiveOS Core)
The foundational platform hosting all services: API Gateway, Skill Executor, Workflow Runner, Knowledge Service, Capability Service, AI Provider Service, Execution History Service, Domain Pack Manager, Configuration Service. Business-agnostic.

## Relationship Map

```
Business
  │
  ├── Organisation Brain (query-time merge)
  │    ├── Domain Pack(s)
  │    │    ├── Domain Knowledge
  │    │    ├── Skills (declarative YAML)
  │    │    └── Workflow Templates (declarative YAML)
  │    ├── Organisation Knowledge (customer-owned)
  │    ├── Custom Skills (V2+)
  │    └── Custom Workflows (V2+)
  │
  ├── Core Services
  │    ├── Domain Pack Manager (lifecycle)
  │    ├── Knowledge Service (index + search)
  │    ├── Capability Service (system functions)
  │    ├── AI Provider Service (model abstraction)
  │    ├── Skill Executor (orchestration)
  │    ├── Workflow Runner (sequencing)
  │    ├── Execution History (persistence)
  │    ├── Configuration Service
  │    └── API Gateway
  │
  ├── Knowledge → Capabilities → Skills → Workflows
  │    (Conceptual data/execution pipeline)
  │
  └── Execution History → Future Learning (V2+)
```

## Knowledge Flow

```
Knowledge Pipeline:
  Domain Pack Knowledge (read-only, immutable)
      + Organization Knowledge (mutable, customer)
      = Unified Index (source-tagged query-time join)
          → KnowledgeSearch Capability
              → Skill Executor (prompt compilation)
                  → AI Provider
                      → Output Validation
                          → Execution History
```

---

# 4. Architecture Decisions

## ADR-0001: Declarative Domain Packs
- **Decision:** Domain Packs contain only declarative content (YAML, Markdown). No executable code.
- **Why:** Security (no execution surface), portability (directory of files), authorability (domain experts without engineering), platform independence.
- **Rejected:** Python packages (security risk, authorship barrier), database dumps (no VCS/inspectability), custom binary (complexity).
- **Related docs:** PD-01, PD-12, Domain Pack Spec §3, §4, A3 (Declarative Boundaries), P8 (Declarative over Imperative).

## ADR-0002: Execution Over Learning in V1
- **Decision:** V1 ships execution history collection only. Pattern detection, recommendation, learning from rejection deferred to V2.
- **Why:** Learning requires data that doesn't exist at launch. Execution History serves immediate V1 debugging/audit needs and is the necessary V2 foundation. Removes ~40% V1 engineering effort.
- **Rejected:** Building pattern detection in V1 (premature optimization without data).
- **Related docs:** PD-02, Product Scope V1/V2, Execution History Spec, P1 (Simplicity), P4 (Practical Value).

## ADR-0003: AI Provider Abstraction
- **Decision:** Core defines an AI Provider interface. Provider adapters implement it. Skill Executor communicates only with the interface.
- **Why:** Decouples Core from vendor-specific models. Enables on-premise-first (local models default) while allowing cloud upgrade path. New providers (Claude, Gemini) added via adapters without Core changes.
- **Rejected:** Direct coupling to one provider (vendor lock-in, violates P6/P7).
- **Related docs:** PD-03, AI Provider Spec, Runtime Architecture §3, P6 (On-Premise First), P7 (Extensibility).

## ADR-0004: Capability Layer Between Knowledge and Skills
- **Decision:** A Capability Layer sits between Knowledge and Skills. Capabilities are reusable system-level functions owned by Core. Skills declare required capabilities by ID.
- **Why:** Prevents Skill reinvention of common functions. Keeps Skills declarative. Enables capability reuse across Skills and Domain Packs.
- **Rejected:** Skills calling system services directly (defeats declarative purity, couples Skills to implementation).
- **Related docs:** PD-04, Capability Layer Spec, Skill Spec §3, P3 (Modularity), P8 (Declarative).

## ADR-0005: Skill Executor as Central Orchestrator
- **Decision:** The Skill Executor is the single, central orchestrator for all Skill executions. Handles full lifecycle: load → validate → prepare → compile → invoke AI → parse → record → return.
- **Why:** Single execution path ensures consistent behavior, debugging, auditing. Prevents dual-engine problem.
- **Rejected:** Distributed execution logic across components (creates multiple execution paths to debug/maintain).
- **Related docs:** PD-05, Runtime Architecture §3, Skill Spec §5, A1 (Single Execution Path).

## ADR-0006: Workflow Runner Reuses Skill Executor
- **Decision:** Workflow Runner does NOT implement Skill execution logic. It is a pure orchestrator that calls Skill Executor for each step.
- **Why:** Preserves single execution path (A1). Eliminates duplication. Any Skill execution enhancement automatically benefits Workflows.
- **Rejected:** Workflow Runner with its own Skill execution (dual-engine problem, diverging behavior).
- **Related docs:** PD-06, Workflow Spec §2, §5, Runtime Architecture §3, A1 (Single Execution Path).

## ADR-0007: Single Knowledge Index with Source Tagging
- **Decision:** Single searchable knowledge index. Every document tagged with source type (`domain:` or `org:`). Tags enable future split if needed.
- **Why:** V1 does not need a merge layer. Simple, fast, buildable in days. Tags preserve conceptual separation. Migration path to separate indexes if V2 requires it.
- **Rejected:** Separate indexes with merge layer (over-engineered for V1), hybrid approach (unnecessary complexity with one Domain Pack).
- **Related docs:** PD-07, Domain Pack Spec §8, P3 (Modularity), A10 (Storage Separation).

## ADR-0008: On-Premise Default Deployment
- **Decision:** HiveOS deploys on customer infrastructure by default. Cloud AI is optional, explicitly configured. Remote access is for management/monitoring only.
- **Why:** Data sovereignty is non-negotiable. Enterprise/regulated customers require on-premise. On-premise→cloud is simpler than reverse.
- **Rejected:** SaaS-first (violates P6/P9, excludes regulated customers), cloud-optional (default path determines architecture).
- **Related docs:** PD-08, Product Bible §9, P6 (On-Premise First), P9 (Data Sovereignty), AI Provider Spec §4.

## ADR-0009: Embedded Prompts in V1 Skills
- **Decision:** Prompts embedded directly inside Skill YAML `instruction` field. Separate prompt asset files deferred to V2.
- **Why:** V1 has ~5 Skills. Separate prompt files double file count for no benefit. Refactoring 5 files is an afternoon's work.
- **Rejected:** Extracting prompts to separate files now (premature file management complexity).
- **Related docs:** PD-09, Skill Spec §3, DD-005 (Deferred Decision).

## ADR-0010: Flat Domain Pack Directory Structure
- **Decision:** V1 Domain Packs use flat directory structure (max one level nesting). `knowledge/`, `skills/`, `workflows/` top-level, files directly inside.
- **Why:** Simple to understand, author, parse. Nesting can be added backward-compatibly later.
- **Rejected:** Nested directories (unnecessary for ~5 Skills, ~20 knowledge files), deep hierarchy (complex parser, hard to understand at a glance).
- **Related docs:** PD-10, Domain Pack Spec §5, P1 (Simplicity).

## ADR-0011: Execution Context Object
- **Decision:** Every execution creates an Execution Context object — the single container for all state. Complete Context persisted by Execution History Service.
- **Why:** Single source of truth per execution. Simplifies debugging. Directly feeds audit. Enables execution replay, error investigation, future pattern detection.
- **Rejected:** Scattered state across components (no single audit source, harder to debug), partial persistence (missing data for V2 learning).
- **Related docs:** PD-11, Runtime Architecture §3, Execution History Spec §2, Skill Spec §5.

## ADR-0012: No Executable Code in Domain Packs
- **Decision:** Absolute prohibition: Domain Packs contain zero executable code. Declarative content only.
- **Why:** Security (supply chain attack surface), portability (code couples packs to runtime), authorship (domain experts need no engineering), boundary clarity (clean Core/App boundary).
- **Rejected:** Python plugins, shell scripts, compiled binaries, any code in packs.
- **Related docs:** PD-01, PD-12, Domain Pack Spec §3, P8 (Declarative over Imperative).

## ADR-0013: Simplified RBAC in V1
- **Decision:** Single boolean: `is_admin`. Admin: install packs, manage knowledge, configure system. User: search knowledge, run Skills, run Workflows.
- **Why:** V1 has one Business with small team. Complex RBAC = 2-3 weeks of engineering before any customer needs it.
- **Rejected:** Full RBAC with roles, permissions, resource-level control (over-engineered for V1).
- **Related docs:** PD-13, Product Scope V1, P10 (Buildability).

## ADR-0014: No Visual Workflow Builder in V1
- **Decision:** V1 Playground is a developer debug console (run Skill, inspect prompts, view knowledge, examine AI responses). No visual drag-drop canvas.
- **Why:** V1 customers run pre-built Workflow Templates. Visual builder = months of React engineering serving zero V1 customers.
- **Rejected:** React Flow visual canvas in V1 (serves no V1 customer, huge engineering cost).
- **Related docs:** PD-14, Product Scope V1, DD-003, P4 (Practical Value), P10 (Buildability).

## ADR-0015: Human Ownership of Business Truth
- **Decision:** System never changes business rules autonomously. Every recommendation requires explicit human validation. Disagreement = learning mechanism, not failure.
- **Why:** Core philosophical principle. Trust through transparency. Prevents error amplification. Regulatory compliance requires human oversight.
- **Related docs:** PD-15, Product Bible §6, P2 (Human Ownership), P5 (Augment First), DD-001.

## ADR-0016: Confidence-Based Autonomy Threshold
- **Status:** Deferred to V2+
- **Decision:** Deferred until pattern detection exists with empirical precision data. V1: humans always validate.
- **Why:** Cannot design autonomous adoption without knowing pattern detection quality. False positives at low confidence erode trust before autonomy is granted.
- **Trigger for revisit:** Pattern detection precision >95% in empirical testing + customer demand.
- **Related docs:** DD-001, ADR-0015, P2 (Human Ownership).

---

# 5. Current Runtime Flow

## Complete Execution Path

```
┌───────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                  │
│  (Dashboard / Playground / CLI → Core API Gateway)                   │
│  Payload: skill_id, input_parameters, context (optional)              │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  1. ROUTING (Core API Gateway)                                        │
│  - Authenticate request (Bearer token)                                │
│  - Authorize (admin check for admin operations)                       │
│  - Route to Skill Executor (for /run/skill)                           │
│  - Route to Workflow Runner (for /run/workflow)                       │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  2. WORKFLOW RUNNER (if Workflow request)                             │
│  - Load Workflow definition from Domain Pack                          │
│  - Iterate through steps sequentially                                 │
│  - For each step: resolve input_mapping, call Skill Executor          │
│  - Step failure → Workflow failure (V1)                               │
│  - Resolve output mapping after all steps                             │
│  - Record Workflow-level execution history                            │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  3. EXECUTION CONTEXT CREATION (Skill Executor)                       │
│  - Create ExecutionContext object: uuid, type, skill_id, status=running│
│  - Initialise timestamps (started)                                    │
│  - Store input_parameters                                              │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  4. SKILL DEFINITION LOADING (Skill Executor → SkillLoader)           │
│  - Read Skill YAML from installed Domain Pack                         │
│  - Parse: goal, instruction, input_schema, output_schema,             │
│    required_capabilities, knowledge_requirements, model_config        │
│  - Validate Skill structure                                           │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  5. INPUT VALIDATION (Skill Executor → InputValidator)                │
│  - Validate input_parameters against input_schema (JSON Schema)       │
│  - Type coercion if needed                                            │
│  - Reject on validation failure with clear error                      │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  6. KNOWLEDGE RETRIEVAL (Skill Executor → KnowledgeService)           │
│  - Inspect knowledge_requirements (tags, concepts) from Skill         │
│  - Invoke KnowledgeSearch capability                                  │
│    → CapabilityService → KnowledgeService                             │
│  - Query unified index (Domain + Organization Knowledge)              │
│  - Return results with source tags, relevance scores                  │
│  - Store in ExecutionContext.knowledge_retrieved                      │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  7. PRE-AI CAPABILITY INVOCATION (Skill Executor → CapabilityService) │
│  - Check required_capabilities from Skill                             │
│  - For each pre-AI capability (FileReader, Calculator, etc.):         │
│    - Invoke via CapabilityService                                     │
│    - Store result in ExecutionContext.capability_results              │
│  - Fail if required capability not registered                         │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  8. PROMPT COMPILATION (Skill Executor → PromptCompiler)              │
│  - Assemble prompt from:                                              │
│    - Skill instruction (embedded prompt template)                     │
│    - User input_parameters                                            │
│    - Retrieved knowledge                                              │
│    - Pre-AI capability results                                        │
│  - Store compiled prompt in ExecutionContext.prompt_sent              │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  9. AI INVOCATION (Skill Executor → AIProviderService)                │
│  - Read model config from Skill + global Configuration Service        │
│  - Determine provider (local default, cloud if configured)            │
│  - Invoke AI Provider interface with: prompt, model_id, parameters    │
│  - Provider adapter communicates with actual model (Ollama/OpenAI)    │
│  - Store response in ExecutionContext.ai_response                     │
│  - Record tokens, duration, model_used                                │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 10. OUTPUT PROCESSING (Skill Executor → OutputValidator)              │
│  - Parse AI response (expect structured output matching output_schema)│
│  - Validate against output_schema (JSON Schema)                       │
│  - Store validated output in ExecutionContext.output                  │
│  - On parse/validation failure: record error, set status=failed       │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 11. POST-AI CAPABILITY INVOCATION (if needed)                         │
│  - Any capabilities requiring AI output (e.g., translation)           │
│  - Result stored in ExecutionContext                                  │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 12. EXECUTION HISTORY RECORDING (Skill Executor → ExecutionHistory)   │
│  - Set status = completed | failed                                    │
│  - Set completed_at timestamp                                         │
│  - Send complete ExecutionContext to Execution History Service        │
│  - Persist immutably (append-only)                                    │
│  - Return record_id confirmation                                      │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 13. RESULT RETURN                                                    │
│  - Extract final output from ExecutionContext                         │
│  - Return to caller (Dashboard / Workflow Runner / Playground)        │
│  - Workflow Runner: store step result, continue to next step          │
└───────────────────────────────────────────────────────────────────────┘
```

## State Machine (Skill Execution)

```
CREATED → VALIDATING → PREPARING (Knowledge + Capabilities)
  → COMPILING → INVOKING → PARSING → RECORDING → COMPLETED
                          ↘
                           FAILED (any state — exception, timeout, validation error)
```

## Key Constraints

- Single execution path: all Skill runs go through Skill Executor (A1)
- No automatic retry in V1 (user retries from UI)
- No provider fallback in V1 (if local fails, does not try cloud)
- No streaming in V1 (complete response processing only)
- Workflow step failure = Workflow failure (no error handlers in V1)

---

# 6. Domain Pack Specification

## Directory Layout (V1 — Flat)

```
accounting/
├── domain.yaml              # REQUIRED: Manifest & metadata
├── knowledge/               # REQUIRED: Domain knowledge documents
│   ├── 01-accounting-principles.md
│   ├── 02-tax-rules.md
│   └── 03-chart-of-accounts.md
├── skills/                  # REQUIRED: Skill definitions (one YAML per Skill)
│   ├── validate-invoice.yaml
│   ├── categorize-expense.yaml
│   ├── check-tax-compliance.yaml
│   ├── generate-financial-report.yaml
│   └── summarize-policy.yaml
├── workflows/               # OPTIONAL: Workflow Template definitions
│   ├── invoice-processing.yaml
│   └── month-end-close.yaml
└── icon.png                 # OPTIONAL: Single icon at root
```

**Design rules:**
- Max one level of directory nesting
- No nested `assets/` directories — one icon at root
- Knowledge files are flat Markdown with no subdirectories
- Ontology is implicit in the structure and content of knowledge files (formal ontology YAML is V2+)
- Prompt instructions embedded inside Skill YAML, not separate assets

## Manifest (`domain.yaml`)

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

**Intentionally omitted for V1:** `capabilities`, `dependencies`, `permissions` fields. Added when multi-pack coexistence is needed.

## Skills

Each Skill is a single YAML file in `skills/`. Key structure:

```yaml
id: validate-invoice
name: Validate Invoice
version: 1.0.0
input_schema: { type: object, properties: { invoice_data: ..., supplier_id: ... } }
output_schema: { type: object, properties: { status: ..., flags: ..., confidence: ... } }
knowledge_requirements:
  tags: [invoice_validation, tax_rules, supplier_records]
  concepts: [tax_rate, supplier_category, verification_threshold]
required_capabilities: [knowledge_search, calculator]
model:
  provider: default
  temperature: 0.3
  max_tokens: 2048
instruction: >
  You are an invoice validation assistant... (V1: embedded prompt)
```

## Workflows

V1 Workflows are sequential Skill pipelines. No branching, no parallel, no error handlers.

```yaml
id: invoice-processing
steps:
  - id: validate
    skill_id: validate-invoice
    input_mapping:
      invoice_data: "$.input.invoice_data"
      supplier_id: "$.input.supplier_id"
  - id: categorize
    skill_id: categorize-expense
    input_mapping:
      invoice_data: "$.input.invoice_data"
      validation_result: "$.steps.validate.output"
  # ... more steps
```

## Versioning

- Semver: `MAJOR.MINOR.PATCH`
- `min_core_version` in manifest ensures compatibility
- Domain Pack upgrades replace the pack directory. Organization Knowledge unaffected.
- Custom Skills/Workflows (V2+) unaffected by Domain Pack updates.

## Validation

- Domain Pack Manager validates structure on install: checks `domain.yaml` exists, schema validity, referenced Skill/Workflow files exist
- Mandatory fields: `id`, `version`, `name`, `description`, `min_core_version`, `skills`
- Knowledge tags validated against Knowledge Service indexing conventions

## Lifecycle

| Operation | Behavior |
|-----------|----------|
| **Install** | Pack unpacked into `domains/<id>/`. Core discovers `domain.yaml`, validates structure, registers Knowledge/Skills/Workflows. |
| **Update** | New version replaces old pack directory. Core validates `min_core_version`. Organization Knowledge unaffected. |
| **Enable** | Pack's Knowledge, Skills, Workflows become available to the Organization Brain. |
| **Disable** | Pack's content becomes unavailable. No data loss. Organization Knowledge unaffected. |
| **Remove** | Pack directory deleted. Organization Knowledge and custom content unaffected. |

## Content Ownership Boundaries

| Content | Owner | Mutable? |
|---------|-------|----------|
| Domain Pack files (`knowledge/`, `skills/`, `workflows/`) | HiveOS (pack author) | Read-only after installation |
| Organization Knowledge | Customer | Mutable |
| Custom Skills (V2+) | Customer | Mutable |
| Custom Workflows (V2+) | Customer | Mutable |
| Execution History | System (on behalf of customer) | Append-only |

The Core never writes to Domain Pack files.

## Knowledge Synchronization

- Domain Knowledge: shipped as files in the Domain Pack. Installed once, immutable.
- Organization Knowledge: ingested from customer-provided files (PDF, text). Indexed at ingestion time.
- No live sync in V1 (watch directories for changes deferred to V2).
- Single index with source tags: `domain:` prefix for Domain Knowledge, `org:` for customer knowledge.
- Knowledge merge is query-time only. No persisted merged view.

## Installation Lifecycle

1. User or admin triggers install in Dashboard or via API
2. Domain Pack Manager validates pack: schema check, `min_core_version` check, file structure check
3. Pack files copied to `domains/<id>/` (read-only after copy)
4. Domain Pack Manager registers Skills, Workflows, and Knowledge with their respective services
5. Knowledge Service indexes domain knowledge files with `domain:` source tag
6. Pack marked as active (enabled)

## Update Lifecycle

1. New version of pack downloaded/received
2. Domain Pack Manager validates version compatibility (`min_core_version`)
3. Old pack directory replaced with new version
4. Knowledge re-indexed for Domain Knowledge
5. Skill and Workflow definitions refreshed
6. Organization Knowledge untouched
7. Custom Skills/Workflows (V2+) untouched

## Enable/Disable Lifecycle

- **Disable:** Pack's Skills, Workflows, and Knowledge removed from Organization Brain's active set. No data loss. Pack directory preserved.
- **Enable:** Pack's content restored to Organization Brain. No re-indexing needed (knowledge persisted in index, just flagged active).

## V1 Constraints

- Single Domain Pack per installation
- Flat directory (no nesting)
- No pack-to-pack dependencies
- No capabilities declaration in manifest
- Read-only after installation
- Portability: directory can be copied between installations. No registry, no DB entries, no compilation. All internal references relative to pack root.

---

# 7. Current Documentation Status

## `docs/01-Product/` (20 files) — ALL APPROVED AND FROZEN

| # | File | Purpose | Status | Missing |
|---|------|---------|--------|---------|
| 00 | Index.md | Master index | Approved | None |
| 01 | Product-Bible.md | Core identity, philosophy, definitions | Approved | None |
| 02 | Product-Principles.md | 10 principles with conflict resolution | Approved | None |
| 03 | Product-Glossary.md | All defined concepts | Approved | None |
| 04 | Product-Vision.md | Elevator pitch, five pillars, target audience | Approved | None |
| 05 | Product-Scope.md | V1/V2/Long Term boundaries | Approved | None |
| 06 | Product-Decisions.md | Decision register (PD-01 to PD-16) | Approved | None |
| 07 | Architecture-Principles.md | 10 architecture principles (A1-A10) | Approved | None |
| 08 | Runtime-Architecture.md | Core services, skill/workflow lifecycle, seq diagrams | Approved | None |
| 09 | Domain-Pack-Specification.md | Purpose, structure, lifecycle, portability | Approved | None |
| 10 | Capability-Layer-Specification.md | Interface, V1 capabilities, design rules | Approved | None |
| 11 | AI-Provider-Specification.md | Interface, adapters, configuration | Approved | None |
| 12 | Execution-History-Specification.md | What's recorded, storage, API, V1/V2 uses | Approved | None |
| 13 | Skill-Specification.md | Definition, YAML format, lifecycle, granularity | Approved | None |
| 14 | Workflow-Specification.md | Definition, principle, V1 format, constraints | Approved | None |
| 15 | Documentation-Constitution.md | Document governance rules | Approved | None |
| 16 | Assumptions.md | 11 explicit assumptions (A-001 to A-011) | Approved | None |
| 17 | Open-Questions.md | 9 unresolved questions (Q-001 to Q-009) | **Draft** | Answers pending Phase 1 design |
| 18 | Deferred-Decisions.md | 8 deferred decisions (DD-001 to DD-008) | Approved | None |
| 19 | Future-Research-Topics.md | 7 research topics (FR-001 to FR-007) | **Draft** | Research not started |
| 20 | Traceability-Matrix.md | Vision→Principles→Decisions→ADR mapping | Approved | None |

## `docs/ADR/` (16 files) — ALL WRITTEN AND FROZEN

| ADR | Title | Status |
|-----|-------|--------|
| 0001 | Declarative Domain Packs | Approved |
| 0002 | Execution Over Learning in V1 | Approved |
| 0003 | AI Provider Abstraction | Approved |
| 0004 | Capability Layer | Approved |
| 0005 | Skill Executor Central Orchestrator | Approved |
| 0006 | Workflow Runner Reuses Skill Executor | Approved |
| 0007 | Single Knowledge Index w/ Tagging | Approved |
| 0008 | On-Premise Default | Approved |
| 0009 | Embedded Prompts V1 | Approved |
| 0010 | Flat Directory Structure | Approved |
| 0011 | Execution Context Object | Approved |
| 0012 | No Code in Domain Packs | Approved |
| 0013 | Simplified RBAC V1 | Approved |
| 0014 | No Visual Workflow Builder V1 | Approved |
| 0015 | Human Ownership of Truth | Approved |
| 0016 | Confidence Autonomy Threshold | **Deferred** |

## `docs/02-Architecture/` (13 files) — ALL OUTLINES ONLY, CONTENT PENDING

| # | File | Purpose | Status | Missing Sections |
|---|------|---------|--------|------------------|
| 00 | Index.md | Architecture doc index with ADR map | Draft (outline) | Full content |
| 01 | System-Vision.md | Distilled product vision for engineers | **Outline only** | Full ~600 line content not written |
| 02 | System-Architecture.md | C4-level component diagram, service map | **Outline only** | Diagrams, full ~500 line content, port definitions |
| 03 | Runtime-Execution.md | Skill/Workflow execution lifecycle | **Outline only** | State machines schemas, phase boundaries, ~800 line content |
| 04 | Domain-Pack-Specification.md | Schema, file format spec, lifecycle | **Outline only** | JSON schemas, validation rules, ~700 line content |
| 05 | Core-Services.md | Every service interface, state, invariants | **Outline only** | Full ~2000 line content, method signatures, error conditions |
| 06 | API-Reference.md | External HTTP contracts | **Outline only** | Full endpoint specs, ~1000 line content |
| 07 | Data-Models.md | All shared JSON schemas | **Outline only** | Full ~600 line JSON Schema definitions |
| 08 | Contracts.md | Service-to-service conventions | **Outline only** | Full ~400 line conventions |
| 09 | Configuration.md | Config keys, defaults, storage | **Outline only** | Full ~300 line config table |
| 10 | Security.md | Auth, RBAC, data isolation | **Outline only** | Full ~400 line threat model |
| 11 | Deployment.md | On-premise deployment guide | **Outline only** | Full ~500 line installation procedure |
| 12 | ADR-Index.md | ADR reference with component mapping | **Outline only** | Full ~200 line index |
| 13 | Developer-Guide.md | Setup, build, test, contribute | **Outline only** | Full ~800 line guide |

## `docs/06-Research/` — Domain Research

- `accounting/` — Iranian accounting domain research. Contains `_index.md` + subdirectories (01-basics, 02-tax, 03-social-security, 04-commerce, 05-auditing, 06-management-accounting, 07-practical-scenarios). In progress.
- `agents/` — Agent-related research.

---

# 8. Open Design Questions

## Q-001: What Is the Pricing Model?
Domain Packs could be sold, licensed, or bundled. Platform could be free with paid Domain Packs, or paid with included packs. **Not defined.**

## Q-002: What Is the Target Customer Size?
V1 targets "organizations with existing IT infrastructure." Is this 10-person firms, 50-person firms, or 500-person enterprises? Deployment model, hardware requirements, and support model differ dramatically. **Not validated.**

## Q-003: Who Is the Primary Buyer?
IT department? Finance director? CEO? External consultant? Buying criteria and decision process differ. **Not validated.**

## Q-004: What Is the Minimum Hardware Required for Local AI?
Running local models requires specific hardware (RAM, GPU/NPU). Minimum spec for reasonable UX is **unknown.** Depends on testing with target models (Llama 3.1, Qwen 2.5).

## Q-005: How Are Domain Packs Distributed?
Separate download? Bundled with installer? In-app purchase? Pulled from registry? **Not designed.** Depends on distribution strategy (Phase 2+).

## Q-006: What Happens When Execution History Exceeds Storage Capacity?
10K+ Skill runs/day → rapid growth. Retention policy, export/archive mechanisms. **Undefined.** Depends on V1 usage patterns.

## Q-007: How Do Custom Skills (V2+) Interact with Domain Pack Updates?
If a Custom Skill depends on a Domain Pack Skill, and the Domain Pack updates with breaking changes — what happens? **Undefined.** Depends on Domain Pack versioning strategy (V2+).

## Q-008: Open Decision — Dashboard: Separate Service or Embedded?
Separate frontend service (like a React app) or embedded HTML served by Core API Gateway? **Deferred to Phase 1 — Core Architecture.**

## Q-009: Open Decision — Configuration: File or Database?
YAML file (simpler, single-user) or database (multi-user admin via Dashboard)? **Deferred to Phase 1 — Core Architecture.**

## Additional Architectural Open Questions

- **Vector search:** What embedding strategy for knowledge search? Single knowledge index suggests a vector + keyword hybrid, but implementation not designed.
- **Plugin system:** How does the Capability Service register new capabilities at runtime? Static registry vs hot-plug?
- **Dashboard tech stack:** React? Svelte? Server-rendered? Not chosen.
- **Local AI orchestration:** Ollama or LM Studio? How is model lifecycle managed (download, configure, serve)?
- **Single process vs multi-process runtime:** A-007 assumes single process sufficient for V1. If not, how to scale?
- **Knowledge ingestion pipeline:** File watcher? Manual upload API? Scheduled crawl? V1 specifies "PDF + text files from directory" but mechanism not detailed.

---

# 9. Deferred Features

## DD-001: Confidence-Based Autonomy Threshold (V2+)
- **What:** HiveOS auto-adopts patterns above confidence threshold without human approval.
- **Why deferred:** Cannot design without knowing pattern detection quality. Need empirical precision data. V1: humans always validate.
- **Trigger:** Pattern detection precision >95%. Customer demand for reduced review.

## DD-002: Multiple Domain Pack Coexistence (V2+)
- **What:** Install and use multiple Domain Packs simultaneously.
- **Why deferred:** V1 ships with one Domain Pack. Cross-pack concerns (ontology merging, conflict resolution, dependencies) not needed until second pack exists.
- **Trigger:** Second Domain Pack enters development.

## DD-003: Visual Workflow Builder (V2+)
- **What:** Drag-and-drop visual flow builder (React Flow canvas).
- **Why deferred:** Months of frontend engineering for zero V1 customers. V1 runs pre-built templates.
- **Trigger:** Customers request custom Workflow composition.

## DD-004: Fine-Grained RBAC (V2+)
- **What:** Multiple roles, resource-level permissions, API key scoping.
- **Why deferred:** V1 has one Business with small team. Boolean admin/user suffices.
- **Trigger:** Customer requires departmental access controls or external auditor review.

## DD-005: Separate Prompt Asset Files (V2+)
- **What:** Extract AI prompts from Skill YAML into separate files with versioning and localization.
- **Why deferred:** V1 has ~5 Skills. Embedded prompts manageable. Extraction adds file management complexity without proportional benefit.
- **Trigger:** Domain Pack >10 Skills. Multi-language prompt support needed.

## DD-006: Two-Way System Integration (V2+)
- **What:** HiveOS writes results back to ERP, CRM, accounting software.
- **Why deferred:** Adds API contracts, auth, error handling, idempotency, consistency guarantees. V1 focuses on intelligence layer (read and process), not execution layer (write back).
- **Trigger:** Customer requires automated posting to accounting system.

## DD-007: Cross-Organization Anonymized Learning (Long Term)
- **What:** Aggregate patterns across opt-in customer installations.
- **Why deferred:** Requires multiple installations, privacy infrastructure, consent, anonymization. Entirely premature for V1.
- **Trigger:** 100+ active HiveOS installations.

## DD-008: Streaming AI Responses (V2+)
- **What:** Token-by-token streaming for real-time UX.
- **Why deferred:** Major complexity to AI Provider interface, Execution Context, UI. V1 processes complete responses. Streaming is UX enhancement, not functional requirement.
- **Trigger:** Customer feedback on response time.

---

# 10. Risks

## Architectural Risks

| Risk | Description | Severity | Mitigation |
|------|-------------|----------|------------|
| **Execution Context schema incompleteness** | If Execution Context misses signals needed for V2 pattern detection, retrofitting is painful (A-010) | HIGH | Design EC with V2 query patterns in mind. Include field placeholders for V2 data. |
| **Single index performance** | Unified knowledge index may degrade at scale if one Domain Pack has 1000s of documents | MEDIUM | Source tags enable migration to separate indexes. Monitor in V1. |
| **Single process bottleneck** | One process may not handle concurrent Skill executions (A-007) | MEDIUM | Service-oriented arch allows horizontal scaling. Monitor and address if needed. |
| **AI Provider interface too narrow** | If interface doesn't support future capabilities (tool calling, multimodal, streaming), breaking change needed | MEDIUM | Design interface with capability declaration (`ProviderCapabilities`). V1: minimal. |
| **Declarative boundary too restrictive** | Some domain logic may genuinely require code. This forces everything into Core Capabilities (ADR-0004, ADR-0012) | MEDIUM | Capability Service designed for extension. Add capabilities as needed. |
| **No error handlers in Workflows** | Single step failure → entire Workflow fails. Brittle for real-world usage | LOW | Acceptable for V1. V2 adds error handlers. |
| **No streaming path** | V1 UI waits for complete AI response. UX degradation for long-running Skills | LOW | Acceptable for V1. V2 adds streaming. |

## Product Risks

| Risk | Description | Severity | Mitigation |
|------|-------------|----------|------------|
| **Local AI quality insufficient** | Open-source models may not meet quality for accounting domain tasks (A-005) | HIGH | Benchmark early. Cloud AI alternative available. May need to recommend cloud for V1. |
| **Single Domain Pack generalizes poorly** | Accounting varies significantly across organizations (A-002) | HIGH | Cover core universal concepts. Organization Knowledge ingestion handles customization. |
| **On-premise deployment too complex** | Target customers may lack infrastructure/hardware/IT support (A-006) | HIGH | V1 targets organizations with existing IT. Lightweight deployment option for smaller firms deferred. |
| **V1 usage volume insufficient for V2** | If V1 is used as reference tool rather than operational platform, execution volume too low for pattern detection (A-011) | MEDIUM | Skills designed for daily operational use. Marketing focuses on productivity. |
| **Domain expert assumption invalid** | Domain experts may not actively review pattern recommendations in V2 (A-004) | MEDIUM | V2 should consider notification design and feedback incentives. |
| **Observed behavior may be wrong** | System could learn and reinforce bad practices if people take suboptimal shortcuts (A-003) | MEDIUM | Human validation gate (V2) catches false patterns. EC captures outcome, not just action. |

## Implementation Risks

| Risk | Description | Severity | Mitigation |
|------|-------------|----------|------------|
| **Scope creep during Phase 1** | Adding features beyond V1 scope during architecture design | HIGH | Frozen Product Scope (05). ADR required for V1 additions with tradeoff assessment. |
| **Skill Executor becomes God object** | Central orchestrator (ADR-0005) could accumulate non-execution concerns | MEDIUM | Clear sub-phase decomposition (7 sub-phases). Interface stability enforcement. |
| **Domain Pack format changes after V1** | If Domain Pack format needs breaking changes, installed packs break | MEDIUM | `min_core_version` in manifest. Versioned Skill/Workflow schemas. |
| **Knowledge Service becomes read-only dead end** | V1 has no write path for Organization Knowledge beyond initial ingestion | LOW | Acceptable for V1. V2 adds full Knowledge CRUD. |
| **Dashboard built with wrong stack** | Choice of frontend framework locked in before team has enough data | LOW | Deferred to Phase 1 architecture. |
| **Old codebase still referenced** | "Old implementation codebase deprecated" means there may be stale code confusing new developers | MEDIUM | Clear deprecation markers. Consider archiving old code. |

---

# 11. Immediate Next Steps

Implementation roadmap from Phase 1 (Core Architecture) start. Ordered by architectural value — each task enables the next.

## Task 1: 02-System-Architecture — Full Content Write
**What:** Write the C4-level component diagram. Every Core service, their boundaries, communication paths, data stores, deployment boundary. 500 lines.
**Why before everything else:** The system architecture is the map. Every other technical document depends on knowing what services exist and how they connect. Without this, component interfaces (05), API contracts (06), data models (07) have no anchor.
**Prerequisite:** Only the frozen Product docs (already done).

## Task 2: 03-Runtime-Execution — Full Content Write
**What:** Complete execution lifecycle with state machines. Skill state machine (CREATED→COMPLETED/FAILED), Workflow state machine, Execution Context lifecycle, timeout policy, error propagation rules. 800 lines + Mermaid diagrams.
**Why next:** After we know WHAT services exist (Task 1), we need to know HOW they interact during execution. This document is the runtime bible — every service implementation references it.
**Dependency:** 02-System-Architecture (Task 1).

## Task 3: 07-Data-Models — Full Content Write
**What:** Formal JSON Schema definitions for every shared data model: ExecutionContext, ExecutionRecord, SkillDefinition, WorkflowDefinition, DomainPackMetadata, KnowledgeDocument, CapabilityResult, AIProviderResponse, ErrorEnvelope. 600 lines.
**Why next:** Data models are the shared language of the system. API contracts (Task 5), service interfaces (Task 4), and execution logic all reference these schemas. Writing schemas early prevents integration mismatches.
**Dependency:** 03-Runtime-Execution (Execution Context schema binds to lifecycle).

## Task 4: 05-Core-Services — Full Content Write
**What:** Per-service interface definitions with method signatures, input/output schemas, state, invariants, error conditions, extension points. 2000 lines (largest document).
**Why next:** After the component map (Task 1), runtime flow (Task 2), and shared data models (Task 3), we can define each service's contract with precision. This document is what developers implement.
**Dependency:** 02 (service map), 03 (runtime flow → what methods each service needs), 07 (data models → method signatures).

## Task 5: 06-API-Reference — Full Content Write
**What:** Complete external HTTP API contracts: every endpoint, method, path, request/response body, status code, error condition. 1000 lines.
**Why next:** The API is the contract between Core and Dashboard/CLI/integrations. Should be written after service interfaces (Task 4) are stable — API routes map to service methods.
**Dependency:** 05-Core-Services (each API endpoint wraps a service method).

## Task 6: 04-Domain-Pack-Specification — Full Content Write
**What:** Technical format spec with JSON schemas for domain.yaml, Skill YAML, Workflow YAML, knowledge frontmatter. Pack lifecycle state machine. Validation rules. 700 lines.
**Why next:** Domain Pack format is the developer-facing contract for pack authors. Must be stable before first Domain Pack (Accounting) is authored.
**Dependency:** 07-Data-Models (Skill/Workflow schemas already defined there), domain.yaml schema in 07.

## Task 7: 08-Contracts — Full Content Write
**What:** Service-to-service communication conventions: ID format, error envelope, schema versioning, timestamp format, pagination. 400 lines.
**Why next:** All services share these conventions. Should be finalized before implementation starts, but depends on understanding the data models (Task 3).
**Dependency:** 07-Data-Models (ErrorEnvelope schema).

## Task 8: 09-Configuration — Full Content Write
**What:** Full config key table with types, defaults, scope. Config file format, env var overrides. 300 lines.
**Why next:** Before deployment guide (Task 9) and implementation (Task 10), we need to know what configuration the system requires. Relatively independent — can be done in parallel with Tasks 5-7.
**Dependency:** 05-Core-Services (config keys consumed by services).

## Task 9: 10-Security — Full Content Write
**What:** Threat model, V1 auth/authorization, data isolation, Domain Pack safety, network security. 400 lines.
**Why next:** Security affects API Gateway design, Domain Pack Manager, and knowledge storage. Must be specified before implementation.
**Dependency:** 05-Core-Services (auth middleware), 07 (data isolation model).

## Task 10: 11-Deployment — Full Content Write
**What:** Hardware requirements, Docker/native install, configuration, verification, upgrade, backup/restore, troubleshooting. 500 lines.
**Why next:** Deployment doc is read by ops, not developers. Lower dependency chain priority.
**Dependency:** 09-Configuration, 10-Security.

## Task 11: 12-ADR-Index — Full Content Write
**What:** ADR-to-component mapping table. 200 lines. Relatively simple — depends on all other docs being written to verify component mapping.
**Dependency:** All preceding docs.

## Task 12: 13-Developer-Guide — Full Content Write
**What:** Setup, build, test, contribute guide. 800 lines. Can be written once all other docs exist and implementation pattern is clear.
**Dependency:** All preceding docs.

## Tasks 13-17: Implementation
After all 02-Architecture docs are written:
1. **Knowledge Service** + search index — simplest service, foundation for others
2. **Configuration Service** — needed by every other service
3. **Domain Pack Manager** — need pack lifecycle to test Skills
4. **Capability Service** — four V1 capabilities
5. **AI Provider Service** — local + cloud adapters
6. **Execution History Service** — append-only storage
7. **Skill Executor** — central orchestrator (most complex, depends on all above)
8. **Workflow Runner** — depends on Skill Executor
9. **Core API Gateway** — wraps all services
10. **Dashboard** — frontend UI
11. **Accounting Domain Pack** — requires stable pack format + Skill Executor

---

# 12. Financial Domain Status

## What Is Already Designed

**Product level (01-Product/):**
- The Accounting Domain Pack is the V1 pack: 5 Skills (Validate Invoice, Categorize Expense, Check Tax Compliance, Generate Financial Report, Summarize Policy)
- 2 Workflow Templates (Invoice Processing, Month-End Close)
- 20-30 knowledge documents covering concepts needed by the 5 Skills
- Domain manifest example (domain.yaml) in Domain Pack Spec §6 shows accounting-specific content
- Knowledge documents: accounting principles, tax rules, chart of accounts
- Capabilities required: KnowledgeSearch, Calculator, FileReader (for invoice data)
- Target audience: Iranian accounting firms (Product Vision §Target Audience)

**Research level (06-Research/):**
- `docs/06-Research/accounting/` directory exists with structure:
  - `_index.md` — master index of accounting research
  - `01-basics/` — accounting fundamentals
  - `02-tax/` — Iranian tax regulations
  - `03-social-security/` — social security compliance
  - `04-commerce/` — commerce-related accounting
  - `05-auditing/` — auditing standards
  - `06-management-accounting/` — management accounting
  - `07-practical-scenarios/` — real-world use cases
- Research is in progress (FR-004: Iranian Accounting Domain Specifics)

**Knowledge vault (D:\mind\accounting\):**
- 1054 markdown + 341 PDF + 6 Excel files (822MB) of accounting knowledge content
- Structured and cataloged via `_build/_stages/03-structured.json`
- SHA-256 deduplication, pure knowledge-only doctrine (no promotional content)

## What Still Needs to Be Designed

**Domain Pack authoring:**
- The actual 5 Skill YAML files with full prompts, schemas, knowledge requirements, and capability declarations
- The 2 Workflow Templates with step definitions and input mappings
- The 20-30 knowledge documents in Domain Pack format (Markdown with frontmatter and tagging)
- The `domain.yaml` manifest file
- Icon and metadata

**Domain-specific design decisions:**
- Persian language prompt engineering for accounting Skills (how to prompt local models in Persian)
- Chart of accounts structure appropriate for Iranian accounting
- Tax rate tables and rule representations
- Invoice data schema (what fields does an Iranian invoice have?)
- Supplier record schema for validation
- Knowledge tagging taxonomy specific to accounting

**Research gaps (FR-004):**
- Iranian GAAP vs IFRS differences — need clear documentation
- Tax regulation specifics (value-added tax, corporate tax, withholding tax)
- Common accounting software in Iranian market — integration implications
- Typical firm size and workflow patterns
- Pain points where AI adds immediate value

## Business Capabilities This First Pack Should Eventually Support

V1 capabilities the Accounting pack should eventually support:
- Invoice validation (cross-reference supplier, tax rules, policy)
- Expense categorization (automated classification)
- Tax compliance checking (regulatory adherence)
- Financial report generation (structured reports from data)
- Policy summarization (natural language policy Q&A)
- Invoice processing workflow (validate → categorize → check compliance → record)
- Month-end close workflow (categorize expenses → check compliance → generate report)

V2+ capabilities the Accounting pack should support:
- Account reconciliation support (detect discrepancies)
- Audit trail analysis (flag unusual patterns)
- Cash flow forecasting (from historical patterns)
- Regulatory filing preparation
- Fraud detection patterns (from execution history)
- Multi-period financial comparison

## What Should NOT Be Attempted in V1 for Financial Domain

- Direct integration with Iranian accounting software (e.g., Hedasoft, Sepidar) — requires APIs that may not exist or are proprietary. **DD-006 deferred.**
- OCR of scanned invoice images — requires image capability (V2). V1 assumes digital/structured invoice data.
- Automated posting to accounting ledger — two-way integration (V2).
- Cross-period trend detection — requires pattern detection (V2).
- Full IFRS/IAS compliance engine — deep ontology work (V2+).
- Multi-company consolidation — multi-Business scope (Long Term).
- Real-time bank reconciliation — requires live data connectivity (V2+).

---

# 13. Final Assessment

## What Another Engineering Team Needs to Know

1. **Phase 0 is done.** Product Discovery is complete and frozen at `docs/01-Product/` (20 documents) and `docs/ADR/` (16 records). These are the source of truth for *what* to build and *why*.

2. **Phase 1 is outlineless.** `docs/02-Architecture/` has 13 documents, all at *outline stage only*. Full content (estimated 8,500+ lines total) needs to be written before any code is touched.

3. **The old implementation is deprecated.** The codebase at `hiveos-financial-brain` may contain useful reference code but the product definition was refocused and the old code may not match the new architecture. Do not assume the existing codebase is the canonical implementation.

4. **The first Domain Pack is Accounting/Iranian accounting.** Research materials at `docs/06-Research/accounting/` and the knowledge vault at `D:\mind\accounting\`. The pack format is defined at the product level but needs technical specification (04-Domain-Pack-Specification content).

5. **V1 is strictly a productivity platform.** No learning, no pattern detection, no custom authoring, no visual builder. Every execution goes through the Skill Executor. Everything is recorded in Execution History for future learning.

6. **Domain Packs contain zero code.** Absolutely no executable content. All interaction is through declared Capabilities (KnowledgeSearch, FileReader, WebAccess, Calculator) and AI prompts embedded in Skill YAML.

7. **On-premise first.** Local AI models (Ollama/LM Studio) are the default. Cloud AI is an explicitly configured option. All data stays on customer infrastructure.

8. **The project lives at `C:\Users\Hossein Mobini\Desktop\hive-os\`.** AGENTS.md is the boot file. Git at `origin/main` on `hiveos-financial-brain`. Current HEAD `57fe0cc`, latest tag `v0.12.0`.

## Assumptions That Must Never Be Violated

1. **Domain Packs are declarative only** (ADR-0001, ADR-0012). No code ever crosses the Core↔Domain Pack boundary. This is an absolute prohibition, not a guideline.

2. **The Skill Executor is the single execution path** (ADR-0005, A1). No component ever implements parallel Skill execution logic. The Workflow Runner calls the Skill Executor — it does not run Skills itself.

3. **Execution History is append-only and complete** (ADR-0002, ADR-0011). Every execution is recorded with full context (inputs, outputs, prompts, responses, knowledge, errors). Records are never modified. This data is the foundation for V2 learning.

4. **Humans own the truth** (ADR-0015). The system never changes business rules autonomously. Every recommendation requires human validation. This is the core philosophical tenet.

5. **Storage separation is maintained** (A10). Domain Pack content (read-only, immutable) and Organization Knowledge (mutable, customer-owned) are stored separately. The "merge" is a query-time operation. Core never writes to Domain Pack files.

6. **Data sovereignty is non-negotiable** (P6, P9, ADR-0008). On-premise is the default. Cloud AI is optional and explicitly configured. No data leaves customer infrastructure without customer choice.

7. **Documents are the source of truth** (Documentation Constitution, Rule 1). If a conversation produces a decision, it must be in the docs within the same session. Undocumented decisions do not exist.

## Source of Truth Documents

| Layer | Document | Status |
|-------|----------|--------|
| **Identity & Philosophy** | `docs/01-Product/01-Product-Bible.md` | Approved |
| **Principles** | `docs/01-Product/02-Product-Principles.md` | Approved |
| *Architecture Principles* | `docs/01-Product/07-Architecture-Principles.md` | Approved |
| **Glossary** | `docs/01-Product/03-Product-Glossary.md` | Approved |
| **Vision** | `docs/01-Product/04-Product-Vision.md` | Approved |
| **Scope** | `docs/01-Product/05-Product-Scope.md` | Approved |
| **Product Decisions** | `docs/01-Product/06-Product-Decisions.md` | Approved |
| **ADRs** | `docs/ADR/` (16 files) | 15 Approved, 1 Deferred |
| **Traceability** | `docs/01-Product/20-Traceability-Matrix.md` | Approved |
| **Assumptions** | `docs/01-Product/16-Assumptions.md` | Approved |
| **Open Questions** | `docs/01-Product/17-Open-Questions.md` | **Draft** |
| **Deferred Decisions** | `docs/01-Product/18-Deferred-Decisions.md` | Approved |
| **Future Research** | `docs/01-Product/19-Future-Research-Topics.md` | **Draft** |
| **Doc Constitution** | `docs/01-Product/15-Documentation-Constitution.md` | Approved |
| **Runtime (Product)** | `docs/01-Product/08-Runtime-Architecture.md` | Approved |
| **Domain Pack (Product)** | `docs/01-Product/09-Domain-Pack-Specification.md` | Approved |
| **Capability Layer** | `docs/01-Product/10-Capability-Layer-Specification.md` | Approved |
| **AI Provider** | `docs/01-Product/11-AI-Provider-Specification.md` | Approved |
| **Execution History** | `docs/01-Product/12-Execution-History-Specification.md` | Approved |
| **Skill Spec** | `docs/01-Product/13-Skill-Specification.md` | Approved |
| **Workflow Spec** | `docs/01-Product/14-Workflow-Specification.md` | Approved |
| _Tech Architecture (outlines)_ | `docs/02-Architecture/` (13 files) | _Outline only_ |
| _Research_ | `docs/06-Research/accounting/` | _In progress_ |

## Five Most Important Architectural Decisions

1. **ADR-0005: Skill Executor as Central Orchestrator** — All execution flows through one component. This decision defines the entire runtime architecture. Every other service supports the Skill Executor.

2. **ADR-0001 + ADR-0012: Domain Packs Are Purely Declarative** — The clean Core↔Domain Pack boundary prevents security vulnerabilities, ensures portability, and enables domain expert authorship. This decision shapes the entire extension model.

3. **ADR-0002: Execution Over Learning in V1** — Removes ~40% of V1 engineering effort. Defines what V1 is (productivity platform) vs what V2 becomes (intelligence layer). Execution History data collected now is the foundation for everything V2+.

4. **ADR-0007: Single Knowledge Index with Source Tagging** — Balances simplicity (one index) with separation (source tags enable future split). This decision defines how knowledge flows from Domain Packs and customer sources into the Organization Brain.

5. **ADR-0003: AI Provider Abstraction** — Enables on-premise-first architecture while preserving cloud AI as an upgrade path. Protects against vendor lock-in. Makes the system deployable in air-gapped environments. This decision defines the entire AI integration model.

---

*End of HiveOS Architecture & Product Memory Snapshot*
*Generated from approved documentation at `docs/01-Product/`, `docs/ADR/`, and `docs/02-Architecture/`*
