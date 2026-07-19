# Product Scope — V1 / V2 / Long Term

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Product Bible (01), Product Principles (02), Product Decisions (06)

---

## Phases Overview

| Phase | Focus | Timeline | Customer Value |
|-------|-------|----------|----------------|
| **V1** | Productivity Platform | Now | Searchable knowledge, pre-built Skills and Workflows |
| **V2** | Intelligence Layer | Next | Pattern detection, custom authoring, multi-domain |
| **Long Term** | Autonomous Organization | Future | Predictive intelligence, marketplace, cross-org learning |

---

## V1 — Productivity Platform

**Tagline:** "Your organization's knowledge, made computable from day one."

V1 is a domain-aware productivity platform. Customers install HiveOS, connect their knowledge, and immediately search across domain expertise and run pre-built skills. Learning infrastructure is limited to execution history collection — enough for debugging and audit, not enough for pattern detection.

### What Ships in V1

#### Core Platform
- [x] On-premise installation
- [x] Single Business per installation
- [x] Admin user account (no fine-grained RBAC)
- [x] Domain Pack Manager (install, enable, disable, remove)
- [x] Knowledge Service (unified search index with source tagging)
- [x] Organization Knowledge ingestion (PDF + text files from directory)
- [x] Skill Executor (load → knowledge → capabilities → AI → validate → record)
- [x] AI Provider interface with local model adapter (default)
- [x] AI Provider cloud adapter (configurable option, one implementation)
- [x] Capability Service with Core Capabilities (KnowledgeSearch, FileReader, WebAccess, Calculator)
- [x] Execution History Service (immutable audit of every execution)
- [x] Workflow Runner (sequential Skill pipeline)
- [x] Configuration Service (system-wide settings)
- [x] Core API Gateway (HTTP/WebSocket entry point)

#### Dashboard
- [x] Searchable Knowledge Workspace
- [x] Skill invocation (single Skill run)
- [x] Workflow Template invocation (pre-built sequences)
- [x] Execution History log view
- [x] Skill/Workflow Test Console ("Playground" — debug run, view prompts, inspect results)
- [x] Domain Pack management UI

#### Accounting Domain Pack (V1)
- [x] Domain manifest (domain.yaml)
- [x] 5 core Skills: Validate Invoice, Categorize Expense, Check Tax Compliance, Generate Financial Report, Summarize Policy
- [x] 2 Workflow Templates: Invoice Processing, Month-End Close
- [x] 20-30 knowledge documents covering concepts needed by the 5 Skills
- [x] Simplified flat directory structure

### Explicitly NOT in V1
- [ ] Pattern detection and recommendation engine
- [ ] Custom Skill authoring by end-users
- [ ] Custom Workflow builder (visual or declarative)
- [ ] Learning from rejection
- [ ] Multiple Domain Pack installation and cross-pack orchestration
- [ ] Fine-grained RBAC (roles, permissions, resource-level access)
- [ ] Visual Playground (drag-drop flow builder)
- [ ] System connectors to ERP/CRM/accounting APIs
- [ ] Multiple Businesses per installation
- [ ] Enterprise SSO / LDAP
- [ ] Prompts as separate assets (embedded in Skill YAML)
- [ ] Ontology merger and cross-pack dependency resolution
- [ ] Two-way system integrations (write-back to external systems)
- [ ] Full autonomy — every action requires explicit user request

---

## V2 — Intelligence Layer

**Tagline:** "The system learns how your organization works."

V2 adds the Learning pillar. By now, HiveOS has accumulated execution history from V1 usage. This data becomes the foundation for pattern detection, recommendation, and custom authoring.

### Planned for V2

#### Learning
- [ ] Pattern detection engine (analyzes execution history)
- [ ] Pattern recommendation UI (surface candidates with evidence)
- [ ] Human validation workflow (approve/reject)
- [ ] Learning from rejection (improve pattern detection over time)
- [ ] Confidence scoring for discovered patterns

#### Custom Authoring
- [ ] Custom Skill creation tool (from validated patterns or from scratch)
- [ ] Custom Workflow builder (declarative composition of Skills)
- [ ] Skill and Workflow version management

#### Multi-Domain
- [ ] Multiple Domain Pack installation and coexistence
- [ ] Cross-pack knowledge merging and conflict resolution
- [ ] Workflow orchestration across multiple Domain Packs
- [ ] Domain Pack dependency declaration

#### Platform Expansion
- [ ] Local AI model as primary, cloud AI as documented alternative
- [ ] RBAC expansion (roles beyond admin/user)
- [ ] Organization Knowledge live sync (watch directories for changes)
- [ ] Additional Core Capabilities (OCR, Translation, Database Query)
- [ ] Prompts extracted to separate asset files (multi-language support)
- [ ] Expanded file format support for knowledge ingestion

---

## Long Term — Autonomous Organization

**Tagline:** "An organization that never forgets and continuously improves."

Long-term features are possibilities, not commitments. They will be re-evaluated based on market feedback and product maturity.

### Long-Term Possibilities
- [ ] Confidence-based autonomous pattern adoption (above threshold, auto-accept)
- [ ] Full Organization Brain visualization (3D or interactive graph)
- [ ] Predictive what-if analysis ("if you change this workflow, X% impact on processing time")
- [ ] Domain Pack marketplace (third-party authors)
- [ ] Proactive Skill suggestion from observed behavior
- [ ] Natural language process design ("create a workflow for vendor invoice approval with two-level escalation")
- [ ] Cross-organization anonymized learning (aggregate patterns across opt-in customers)
- [ ] Multi-Business per installation (consultancy serving multiple clients)
- [ ] Two-way system integrations (HiveOS writes results back to ERP/CRM)
- [ ] Full autonomous execution mode (organization configures autonomy level per Skill/Workflow)

---

## Scope Governance

Any feature not listed in V1 above is presumed deferred to V2 or Long Term unless explicitly re-scoped by an Architecture Decision Record (ADR).

Adding a feature to V1 requires:
1. An ADR explaining why it cannot wait
2. Impact assessment on V1 timeline
3. Confirmation that simplifying another V1 feature to compensate

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
