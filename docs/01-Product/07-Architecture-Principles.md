# Architecture Principles

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Product Principles (02), Runtime Architecture (08), Product Decisions (06)

---

These architecture principles derive from the Product Principles. They govern how we build HiveOS, not what we build.

## The Principles

### A1. Single Execution Path
Every Skill execution, whether from Dashboard, Workflow Runner, or Playground, goes through the same Skill Executor. There is exactly one way to run a Skill.

**Rationale:** Prevents the dual-engine problem. Two execution paths means two places to debug, two places to audit, two places to maintain.

### A2. Service-Oriented Internal Architecture
Core services (Skill Executor, Knowledge Service, Capability Service, AI Provider, Execution History) communicate through defined interfaces. No service calls another service's internal implementation.

**Rationale:** Enables independent testing, replacement, and evolution of each service.

### A3. Declarative Boundaries
The boundary between the Core and a Domain Pack is purely declarative. The Core reads YAML and Markdown. Domain Packs contain no code.

**Rationale:** Security, portability, domain expert authorship.

### A4. Immutable Core over Plugin Modification
If a feature requires modifying Core behavior, it should be a Core enhancement, not a Domain Pack plugin. Domain Packs extend the Core through configuration and content, never through code injection.

**Rationale:** Keeps Domain Packs simple and safe. Prevents the platform from becoming a dependency nightmare.

### A5. Local-Only Default
The default configuration runs entirely on local infrastructure with no external network dependencies. Cloud AI provider is a documented configuration option.

**Rationale:** Data sovereignty is non-negotiable. The product must work fully at a customer site with no internet connectivity.

### A6. Observable by Default
Every execution is recorded with full context: inputs, outputs, knowledge retrieved, prompt sent, AI response, duration, errors. Nothing is executed without an audit trail.

**Rationale:** Debugging, compliance, and the foundation for V2 learning infrastructure.

### A7. Fail Explicitly
When a Skill execution fails, the system returns the error with full context. No silent failures, no swallowed exceptions. The Execution Context captures the failure point and reason.

**Rationale:** Debugging depends on knowing exactly where and why something failed.

### A8. Configuration over Hardcoding
Every settable parameter (AI model, provider, knowledge paths, port numbers) is configuration, not code. The Configuration Service provides centralized access.

**Rationale:** On-premise deployments require per-customer configuration without code changes.

### A9. Interface Stability over Implementation Flexibility
Once a service interface is defined and documented, changing it requires an ADR. Implementation can change freely behind the interface.

**Rationale:** Services have multiple consumers. Interface churn breaks the entire platform.

### A10. Storage Separation
Domain Pack content and Organization Knowledge are stored separately. Domain Packs are read-only. Organization Knowledge is customer-owned and mutable. The "merged" view is a query-time operation.

**Rationale:** Prevents upgrades from overwriting customizations. Enables independent backup and restore of customer data.

---

## Principle Conflict Resolution

| Conflict | Resolution |
|----------|-----------|
| A1 (Single Path) vs adding new execution mode | New mode must route through Skill Executor. The Executor interface expands, not the number of executors. |
| A2 (Service Interfaces) vs build speed | Define the interface minimally. Expand later. Interface definition is mandatory; full implementation depth is not. |
| A4 (Immutable Core) vs customer need for extension | If extension is genuinely needed, it becomes a Core capability, not a Domain Pack plugin. |
| A9 (Interface Stability) vs fast iteration | Interface stability applies to public contracts. Internal interfaces can change during V1 development. Stabilize by V1 release. |
| A6 (Observable) vs performance | Observability is mandatory. Performance optimization must not skip audit recording. |

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
