# 12 — ADR Index

> **Version:** 1.1.0  
> **Owner:** Principal Software Architect  
> **Status:** Complete  
> **Last Updated:** 2026-07-24  
> **Upstream Sources:** `docs/ADR/` (all 17 ADRs)  
> **Dependencies:** None (reference document)  
> **Priority:** 7

---

## 1. ADR Index Table

| # | Title | Status | Components Affected | Constraint Type |
|---|-------|--------|---------------------|----------------|
| 0001 | Use Declarative Domain Packs | Approved | Domain Pack Manager | Structural |
| 0002 | Execution Over Learning in V1 | Approved | Execution History, Skill Executor | Strategic |
| 0003 | AI Provider Abstraction | Approved | AI Provider Service | Structural |
| 0004 | Capability Layer Between Knowledge and Skills | Approved | Capability Service, Skill Executor | Structural |
| 0005 | Skill Executor as Central Orchestrator | Approved | Skill Executor | Structural |
| 0006 | Workflow Runner Reuses Skill Executor | Approved | Workflow Runner, Skill Executor | Structural |
| 0007 | Single Knowledge Index with Source Tagging | Approved | Knowledge Service | Structural |
| 0008 | On-Premise Default | Approved | Deployment, Configuration Service | Strategic |
| 0009 | Embedded Prompts in Domain Packs (V1) | Approved | Domain Pack Manager, Skill Executor | Structural |
| 0010 | Flat Domain Pack File Structure | Approved | Domain Pack Manager | Structural |
| 0011 | Execution Context as Single Source of Truth | Approved | Execution History, Skill Executor | Structural |
| 0012 | No Executable Code in Domain Packs | Approved | Domain Pack Manager | Structural |
| 0013 | Simplified RBAC (V1) | Approved | Core API Gateway | Structural |
| 0014 | No Visual Workflow Builder (V1) | Deferred | Dashboard (future) | Strategic |
| 0015 | Human Ownership of Business Truth | Approved | All components | Philosophical |
| 0016 | Confidence-Based Autonomy Threshold | Deferred | DSF, Recommendation Service | Strategic |
| 0018 | Decision Support Framework | Approved | DSF (Monitoring, Analysis, Recommendation Services) | Architectural |

## 2. Component-to-ADR Reverse Map

### 2.1 Skill Executor
- ADR-0005 (central orchestrator)
- ADR-0009 (embedded prompts)
- ADR-0011 (Execution Context)
- ADR-0004 (capability invocation)

### 2.2 Workflow Runner
- ADR-0006 (reuses Skill Executor)

### 2.3 Knowledge Service
- ADR-0007 (single index, source tagging)

### 2.4 Capability Service
- ADR-0004 (capability layer)

### 2.5 AI Provider Service
- ADR-0003 (provider abstraction)

### 2.6 Execution History
- ADR-0002 (execution over learning)
- ADR-0011 (Execution Context)

### 2.7 Domain Pack Manager
- ADR-0001 (declarative packs)
- ADR-0009 (embedded prompts)
- ADR-0010 (flat structure)
- ADR-0012 (no code in packs)

### 2.8 Core API Gateway
- ADR-0013 (RBAC)

### 2.9 Security
- ADR-0013 (RBAC)
- ADR-0015 (human ownership)

### 2.10 Decision Support Framework
- ADR-0018 (four-layer framework)
- ADR-0002 (execution history as foundation)
- ADR-0015 (recommendations, never autonomous actions)
- ADR-0016 (confidence thresholds — deferred)

## 3. ADR Status Summary

| Status | Count | ADR Numbers |
|--------|-------|-------------|
| Approved | 16 | 0001–0013, 0015, 0018 |
| Deferred | 2 | 0014 (builder), 0016 (autonomy threshold) |

## 4. New ADR-0018 Summary

**ADR-0018** defines a four-layer Decision Support Framework generic across all Domain Packs:

| Layer | Service | Function |
|-------|---------|----------|
| Layer 4 | Recommendation | Surface actionable suggestions via Dashboard |
| Layer 3 | Analysis | Detect patterns using built-in engines (trend, frequency, correlation, efficiency, anomaly, cluster) |
| Layer 2 | Monitoring | Observe execution streams via declarative rules |
| Layer 1 | Execution | Existing V1 Execution History (no changes) |

Key constraints:
- Domain Packs configure all layers via declarative YAML only (ADR-0001, ADR-0012)
- System produces recommendations only — never autonomous decisions (ADR-0015)
- Rule-based in V1 (no LLM calls in DSF)
- Builds on existing Execution History infrastructure (ADR-0002)

## Cross-References

| Target | Relationship |
|--------|-------------|
| docs/ADR/ | Full ADR text (upstream source) |
| docs/02-Architecture/02-System-Architecture.md | Components listed in architecture map |
| docs/02-Architecture/05-Core-Services.md | ADR constraints on each service |
| docs/02-Architecture/03-Runtime-Execution.md | Execution History post-recording hook for DSF |
| docs/ADR/0018-decision-support-framework.md | Full DSF specification |
