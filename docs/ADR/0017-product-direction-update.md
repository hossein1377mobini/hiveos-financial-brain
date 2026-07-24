# ADR-0017: Product Direction Update — HiveOS V1

> **Status:** Approved
> **Date:** 2026-07-24
> **Deciders:** Hossein Mobini (Founder), ChatGPT (Advisor), Hermes (Planner)
> **References:** Product Bible (01), Product Scope (05), ADR-0008 (On-Premise), Open Questions (17)

---

## Context

After reviewing the current architecture and comparing with competitors (n8n, Make, Zapier, Dify), the product direction needs to be redefined. HiveOS must evolve from "workflow automation tool" into an "Organizational Intelligence Platform." The previous 5-Pillar model (Knowledge, Skills, Workflows, Learning, Brain) is replaced by a 4-Engine model.

## Decision

### New Identity

**HiveOS is an Organizational Intelligence Platform that learns from organizations, reasons on their knowledge, and helps managers make better decisions.**

### 4-Engine Architecture

```
Knowledge Engine → Learning Engine → Reasoning Engine → Decision Engine
```

| Engine | Responsibility |
|--------|---------------|
| **Knowledge Engine** | Manages Domain Pack knowledge + Organization knowledge |
| **Learning Engine** | Continuously learns from files, events, and user behavior. Builds organizational memory. |
| **Reasoning Engine** | Reasons on knowledge using AI models (RAG, not fine-tuning) |
| **Decision Engine** | Converts reasoning into management suggestions, alerts, and actionable insights |

### Key Principles

1. **Organizational Learning ≠ Model Training**
   - HiveOS reads customer files → builds knowledge graph → uses RAG
   - HiveOS does NOT fine-tune, LoRA, or retrain LLM models
   - Terminology: use "Organizational Learning" / "Knowledge Acquisition", never "Training"

2. **Privacy-First**
   - All customer data stays on customer infrastructure
   - No data leaves the organization unless explicitly configured
   - Influences every architectural decision

3. **Decision Support as Core Differentiator**
   - Execution is just one capability
   - Real value: helping managers make better decisions
   - Four layers: Execution → Monitoring → Analysis → Recommendation

4. **First-Time Experience**
   - No empty dashboard after installation
   - System immediately shows: "Based on this Domain Pack, these are the business processes we know"

5. **Domain Packs = Knowledge + Business Capabilities**
   - Domain Pack contains: Knowledge, Business Ontology, Skills, Workflow Templates, Decision Templates, Best Practices
   - Customer chooses which capabilities to activate
   - Not everything is enabled by default

6. **Workflow Customization**
   - Every workflow is editable
   - Customer can modify, extend, simplify, remove, or create new workflows
   - HiveOS provides initial knowledge; organization adapts it

7. **Organization-Specific Variables**
   - System detects missing information and requests it
   - Examples: departments, approval hierarchy, cost centers, suppliers
   - Auto-extract from customer documents when possible

---

## Phased Implementation

### V1 — Core Intelligence Platform
- Domain Pack Install + Knowledge Retrieval
- Workflow Execution (templates)
- First-Time Experience
- Capability Selection
- Customer File Watch Folder
- Organizational Learning (parse files, build knowledge graph, memory)
- Privacy-First Architecture
- Monitoring Dashboard (basic)

### V1.5 — Decision Support Foundation
- Organization Variables (wizard + auto-detection)
- Workflow Customization (edit templates)
- Simple Decision Support (alerts, status monitoring)

### V2 — Intelligence Layer
- Full Decision Support (Analysis + Recommendation Engine)
- Pattern Detection
- Custom Workflow Creation
- Advanced Organizational Learning

### V3 — Autonomous Intelligence
- Proactive Insights
- Predictive Analytics
- Cross-Organization Learning

---

## Consequences

- Product Scope (doc 05) needs update to reflect new V1/V2 boundaries
- AGENTS.md vision statement needs update
- Existing ADR-0001 (Declarative Domain Packs) remains valid — no executable code
- ADR-0008 (On-Premise) is reinforced by Privacy-First principle
- ROADMAP.md needs complete rewrite
- New ADR needed for: Decision Support Framework, Organizational Learning Pipeline
