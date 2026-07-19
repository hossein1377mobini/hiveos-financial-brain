# Runtime Architecture

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Architecture Principles (07), Skill Specification (13), Workflow Specification (14), AI Provider Specification (11), Capability Layer Specification (10), Execution History Specification (12)

---

## Overview

The HiveOS runtime is a set of cooperating Core services that execute Skills and Workflows. Every execution follows the same path through these services, regardless of how it was initiated (single Skill run, Workflow run, or Playground debug).

## Core Services

```
┌─────────────────────────────────────────────────────────────┐
│                     CORE API GATEWAY                         │
│         HTTP/WebSocket entry point for all requests          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      WORKFLOW RUNNER                         │
│       Iterates through Workflow steps, calls Skill Executor  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      SKILL EXECUTOR                          │
│  Central orchestrator: loads Skill, invokes Capabilities,    │
│  communicates with AI Provider, validates, records history   │
└───┬──────────┬──────────┬──────────┬────────────────────────┘
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐
│KNOWLEDGE│ │CAPABILITY│ │AI      │ │EXECUTION     │
│SERVICE  │ │SERVICE   │ │PROVIDER│ │HISTORY SVC   │
│(Search  │ │(System   │ │SERVICE │ │(Persist      │
│ Index)  │ │Functions)│ │(Model  │ │ExecutionContext│
└────────┘ └────────┘ │Abstrac)│ └──────────────┘
                       └────────┘
```

## Skill Execution Lifecycle

### 1. Request Initialization
- Dashboard, Workflow Runner, or Playground sends a request to the Core API Gateway.
- Request includes: `skill_id`, `input_parameters`, `context` (optional, for Workflow step chaining).
- Gateway routes to Skill Executor.

### 2. Context Creation
- Skill Executor creates an Execution Context object.
- Execution Context carries: `skill_id`, `input_parameters`, `status`, `timestamps`, `knowledge_retrieved`, `capability_results`, `prompt_sent`, `ai_response`, `output`, `errors`.

### 3. Skill Definition Loading
- Skill Executor loads the Skill definition from the installed Domain Pack.
- Definition includes: goal, instruction/prompt, input_schema, output_schema, required_capabilities, knowledge_requirements, model_config.

### 4. Input Preparation
- Skill Executor validates `input_parameters` against the Skill's `input_schema`.
- Basic type coercion and transformation applied.
- Validated parameters added to Execution Context.

### 5. Knowledge Retrieval
- Skill Executor inspects `knowledge_requirements` from Skill definition.
- Invokes `KnowledgeSearch` Capability (provided by Capability Service → Knowledge Service).
- Knowledge Service queries the unified index (Domain + Organization Knowledge).
- Results added to Execution Context.

### 6. Capability Invocation (Pre-AI)
- Skill Executor checks `required_capabilities` from Skill definition.
- For each capability needed before AI execution (e.g., FileReader, Calculator):
  - Invokes the capability through Capability Service.
  - Capability result added to Execution Context.

### 7. Prompt Generation
- Skill Executor constructs the AI prompt:
  - Skill instruction/prompt template.
  - User input_parameters.
  - Retrieved knowledge.
  - Pre-AI capability results.
- Generated prompt stored in Execution Context.

### 8. AI Invocation
- Skill Executor determines AI model and provider from Configuration Service.
- Invokes AI Provider Service with: prompt, model_id, model_parameters.
- AI Provider Service communicates with the configured provider (local or cloud).
- Response stored in Execution Context.

### 9. Output Processing
- Skill Executor receives raw AI response from AI Provider Service.
- Parses and validates against Skill's `output_schema`.
- Validated output added to Execution Context.

### 10. Post-AI Capabilities (if needed)
- Any capabilities required after AI execution (e.g., Translation) are invoked.

### 11. Execution History Recording
- Complete Execution Context sent to Execution History Service.
- Persisted immutably for audit and future learning.

### 12. Result Return
- Final output extracted from Execution Context.
- Returned to caller (Dashboard, Workflow Runner, or Playground).

## Workflow Execution Lifecycle

1. Workflow Runner loads Workflow Template definition from Domain Pack.
2. Workflow Runner iterates through steps sequentially.
3. For each step:
   a. Maps outputs from previous steps as inputs to current step.
   b. Calls Skill Executor with step's `skill_id` and prepared inputs.
   c. Stores step result in Workflow-level context.
4. After all steps complete, Workflow Runner records Workflow-level execution history.
5. Returns final result to caller.

**Key constraint:** The Workflow Runner does not implement Skill execution logic. It is purely an orchestrator of Skill Executor calls.

## Execution Context Object

The Execution Context is the single source of truth for one execution.

```yaml
execution_context:
  id: uuid
  type: "skill" | "workflow"
  skill_id: string
  workflow_id: string (optional)
  status: "running" | "completed" | "failed"
  timestamps:
    started: iso8601
    knowledge_retrieved: iso8601
    ai_invoked: iso8601
    completed: iso8601
  input_parameters: {}
  knowledge_retrieved: []
  capability_results: {}
  prompt_sent: string
  ai_response: string
  output: {}
  errors: []
  user_feedback: null (V2+)
```

## Service Interaction Diagram

```
User                    Dashboard            Core API             Skill Executor        Knowledge    Capability   AI Provider   Exec History
 │                         │                    │                      │                  Svc          Svc          Svc           Svc
 │─── Click "Run Skill"───►│                    │                      │                  │             │            │             │
 │                         │─── POST /run ─────►│                      │                  │             │            │             │
 │                         │                    │─── execute_skill ───►│                  │             │            │             │
 │                         │                    │                      │─── search ──────►│             │            │             │
 │                         │                    │                      │◄──── results ────┤             │            │             │
 │                         │                    │                      │─── capabilities ─┤────────────►│            │             │
 │                         │                    │                      │◄──── results ────┤────────────┤             │             │
 │                         │                    │                      │─── invoke AI ────┤────────────────────────►│             │
 │                         │                    │                      │◄──── response ───┤────────────────────────┤             │
 │                         │                    │                      │─── record ───────┤─────────────────────────────────────►│
 │                         │                    │                      │◄──── stored ─────┤──────────────────────────────────────┤
 │                         │                    │◄──── result ────────┤                  │             │            │             │
 │                         │◄──── result ──────┤                      │                  │             │            │             │
 │◄──── display result ────┤                    │                      │                  │             │            │             │
```

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
