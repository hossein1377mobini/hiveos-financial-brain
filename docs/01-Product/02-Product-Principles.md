# Product Principles

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Product Bible (01), Architecture Principles (07)

---

## Core Principles

These principles govern every product and architectural decision in HiveOS. They are ordered by priority — when two principles conflict, the higher-ranked principle prevails.

### P1. Simplicity over Completeness

Build what is needed now. Do not build for every possible future scenario. A working simple system delivers more value than an unfinished comprehensive one. Every feature must justify its existence in the current product scope.

**In practice:** V1 ships the productivity platform. Pattern detection, custom authoring, and multi-domain coexistence wait for V2.

### P2. Human Ownership of Business Truth

HiveOS never owns business truth. Humans do. The system observes, explains, recommends, and learns. It never silently changes business rules. Every evolution of organizational knowledge must remain explainable, reviewable, and ultimately owned by humans.

**In practice:** Skills produce recommendations, not decisions. Workflows require human checkpoints for critical actions. Pattern acceptance requires explicit human validation.

### P3. Modularity over Coupling

Every component should have a single, well-defined responsibility and communicate through clear interfaces. No component should depend on the internal implementation of another. The system should be understandable by reading one component at a time.

**In practice:** Skill Executor, Knowledge Service, AI Provider, Capability Service, and Execution History are independent services with defined contracts. Domain Packs are completely separate from the Core.

### P4. Practical Business Value over Academic Elegance

Every feature must deliver measurable value to the user. Elegant architecture that does not serve a customer need is waste. The system should be judged by outcomes, not by the beauty of its design.

**In practice:** The V1 Playground is a developer debug console, not a visual flow builder. The knowledge index is a single searchable store, not a multi-layered ontology merger.

### P5. AI Should Augment Humans Before Replacing Them

The default mode is assistance, not automation. AI skills produce outputs that humans review, validate, and act upon. Full autonomy is a future capability that must be earned through trust, not assumed by design.

**In practice:** Every Skill execution shows its reasoning, evidence, and confidence. Workflows include human approval gates. The system never executes autonomously without explicit configuration.

### P6. On-Premise First

The customer's data belongs to the customer. HiveOS must work fully on-premise without requiring external services. Cloud capabilities are optional extensions, not the default path.

**In practice:** Local AI models are the default. Cloud AI providers are a configurable alternative. No telemetry data leaves the customer's infrastructure without explicit consent.

### P7. Extensibility over Specialization

The platform should be extensible without modifying its core. New knowledge domains, AI providers, capabilities, and integrations should be addable through defined interfaces, not by forking or patching the Core.

**In practice:** The AI Provider interface allows any model backend. The Capability interface allows new system functions. The Domain Pack format is designed to be third-party authorable from day one.

### P8. Declarative over Imperative

Domain Packs, Skills, and Workflows should define *what* should happen, not *how*. The Core is responsible for deriving implementation from declared intent. This keeps Domain Packs portable, inspectable, and authorable by domain experts.

**In practice:** Skills declare goal, inputs, outputs, required capabilities, and knowledge requirements. They do not contain code. The Core Skill Executor compiles these declarations into execution requests.

### P9. Data Sovereignty

The customer's knowledge always belongs to the customer. HiveOS should connect to where data lives, not require data to be moved to HiveOS. All knowledge is stored on customer infrastructure by default.

**In practice:** On-premise deployment by default. Local storage for all knowledge. Cloud AI is optional and configurable. No data leaves without explicit customer choice.

### P10. Buildability by a Small Team

Everything must be buildable by 2-3 engineers in 6-9 months for V1. The architecture must be simple enough that a single person can understand, modify, and deploy the entire system. Complexity that requires a larger team is deferred.

**In practice:** V1 scope is ruthlessly minimal. Learning infrastructure is execution history only. Domain Packs ship with 5 core Skills, not 29. The visual workflow builder is deferred. RBAC is admin/user.

---

## Principle Conflict Resolution

When two principles conflict, apply this precedence:

1. P1 (Simplicity) — before all else, keep it simple
2. P6 (On-Premise) — data sovereignty is non-negotiable
3. P2 (Human Ownership) — before autonomy
4. P4 (Practical Value) — before elegance
5. P8 (Declarative) — before imperative approaches
6. P3 (Modularity) — before tight coupling
7. P5 (Augment First) — before automation
8. P7 (Extensibility) — before specialization
9. P10 (Buildability) — over completeness
10. P9 (Sovereignty) — always protected

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |

## Future Considerations

- As the product matures, some principles may need refinement (e.g., P5 as trust increases)
- New principles may be needed for marketplace, multi-tenant, or SaaS deployment models
