# Product Glossary

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Product Bible (01), Product Vision (04)

---

This glossary defines every core concept in HiveOS. Definitions are authoritative. If a term is used inconsistently anywhere else, this document takes precedence.

## Core Concepts

### HiveOS
An organizational intelligence platform. An on-premise intelligence layer that sits above existing business systems. Observes behavior, discovers patterns, recommends formalization, preserves organizational experience, and grows smarter as the organization grows.

### Business
An independent organizational workspace. The security, knowledge, and operational boundary of HiveOS. In V1, one HiveOS installation = one Business. Departments and teams exist inside as logical groups, not separate Businesses.

### Organization Brain
The merged intelligence formed by combining installed Domain Pack(s) + Organization Knowledge + installed Skills + configured Workflows. Unique per customer. This is what makes each HiveOS instance irreplaceable over time. The merge is a query-time join, not a persisted union.

## Knowledge Concepts

### Domain Pack
A pre-built product shipped by HiveOS. Contains shared knowledge, ontology, AI Skills, Workflow Templates, terminology, rules, and best practices for a specific business domain (e.g., Accounting, Tax, HR, Sales). Customers install Domain Packs — they do not author them. Domain Packs are read-only, declarative, and portable.

### Domain Knowledge
Knowledge shipped inside a Domain Pack. Universal best-practice for an industry or function. Immutable after installation. Updated via Domain Pack releases.

### Organization Knowledge
All customer-specific knowledge: documents, policies, spreadsheets, databases, observed behavior patterns. Lives on customer infrastructure. Grows continuously. Owned by the customer.

### Knowledge (conceptual layer)
What the business knows. Passive. Provides context for Skills. Two sources: Domain Packs (pre-built) + Organization Knowledge (customer-specific).

### Knowledge Service
Core platform service that indexes, stores, and searches both Domain Knowledge and Organization Knowledge in a unified index. Each document is tagged with its source (domain: or org:).

## Execution Concepts

### Skill
The smallest reusable business capability. Performs a specific business task using Knowledge. Skills are declarative — they define goal, inputs, outputs, required capabilities, and knowledge requirements. They do not contain executable code. Two origins: Domain Pack Skills (pre-built, shipped) and Custom Skills (created by the organization from observed patterns — V2+).

### Capability
A reusable system-level function owned by the Core. Examples: OCR, Search, Retrieval, Calculator, Web Access, File Reader, Database Query, Translation. Capabilities are the execution primitives that Skills depend on. Skills declare which capabilities they require; the Core provides the implementations.

### Workflow
An orchestration of multiple Skills to achieve a business outcome. Two origins: Domain Pack Workflow Templates (pre-built, industry-standard) and Custom Workflows (built by the organization — V2+). Workflows are declarative sequences of Skill invocations. They do not contain scripts or branching logic in V1.

### AI Provider
An abstraction layer for AI model interaction. The Core defines an AI Provider interface. Each provider adapter (Ollama, LM Studio, OpenAI, Claude, Gemini) implements this interface. The Skill Executor communicates only with the interface, never with specific providers directly.

### Skill Executor
The central orchestrator of a single Skill's lifecycle. Loads Skill definitions, orchestrates Capabilities, interacts with the AI Provider, validates outputs, and records execution history.

### Workflow Runner
Executes Workflow Templates by iterating through Skill steps and calling the Skill Executor for each step. Does not implement its own execution logic for individual Skills. Responsible for passing outputs between steps.

### Execution Context
A structured container that flows through a single Skill or Workflow execution. Holds all inputs, outputs, intermediate data, retrieved knowledge, generated prompts, AI responses, errors, timestamps, and status. Serves as the single source of truth for a single execution. The entire Execution Context is persisted by the Execution History Service.

### Execution History
Immutable record of every Skill and Workflow execution. Contains the complete Execution Context for each run. Stored persistently. Used for debugging, audit, and as the foundation for V2 learning capabilities.

## Pattern and Learning Concepts

### Pattern (V2+)
A recurring behavior observed across multiple instances, with supporting evidence and confidence level. A candidate, not truth. Surfaces for human review. Patterns become organizational knowledge only after explicit human validation.

### Human Validation (V2+)
The process by which a domain expert approves or rejects a discovered pattern. Validated patterns become organizational knowledge. Rejected patterns become learning data.

### Learning from Rejection (V2+)
When a human rejects a pattern, the system records the rejection context. Over time, the system learns boundaries and improves its pattern detection.

## Deployment Concepts

### On-Premise Deployment
The default deployment model. All HiveOS components run on customer infrastructure. Data never leaves the customer's control. Local AI models are the default inference path.

### Cloud AI Provider
An optional, configurable alternative for AI inference. When enabled, only AI inference requests are sent to the chosen provider. Knowledge and business data remain on-premise.

### Data Sovereignty
The principle that customer knowledge always belongs to the customer. HiveOS connects to where data lives rather than requiring data to be moved. Deployment must never force data to leave customer infrastructure.

## Infrastructure Concepts

### Core (HiveOS Core)
The foundational platform that hosts all services: API Gateway, Skill Executor, Workflow Runner, Knowledge Service, Capability Service, AI Provider Service, Execution History Service, Domain Pack Manager, Configuration Service. The Core is business-agnostic.

### Domain Pack Manager
Core service that handles installation, updating, enabling, disabling, and removal of Domain Packs. Works with declarative, file-based Domain Pack directories.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
