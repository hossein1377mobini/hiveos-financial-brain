# Workflow Specification

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Runtime Architecture (08), Skill Specification (13), Domain Pack Specification (09), ADR-0006

---

## 1. Definition

A Workflow is an orchestration of multiple Skills to achieve a business outcome. While Skills are reusable building blocks, Workflows represent complete business processes specific to an organization or domain.

## 2. The Principle: Workflow Runner Reuses Skill Executor

The Workflow Runner does NOT implement Skill execution logic. It is a pure orchestrator. For each step in a Workflow, it calls the Skill Executor — the same path used by single Skill runs. This ensures:

- Single execution path for debugging and audit.
- Consistent behavior between single-Skill and Workflow execution.
- No duplicate execution logic to maintain.
- Workflow-level Execution History composed of individual Skill execution records.

## 3. Workflow Origins

| Origin | Description | V1 Status |
|--------|-------------|-----------|
| **Domain Pack Workflow Template** | Pre-built workflow shipped inside a Domain Pack | ✅ V1 |
| **Custom Workflow** | Created by the organization (from patterns or manually) | 🟡 V2+ |

## 4. Workflow Definition (YAML) — V1

V1 Workflows are sequential Skill pipelines. No branching, no parallel execution, no error handlers.

```yaml
id: invoice-processing
name: Invoice Processing Workflow
description: >
  Processes an incoming invoice from receipt through validation,
  categorization, and recording. Standard daily accounting workflow.
version: 1.0.0

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
  
  - id: check-compliance
    skill_id: check-tax-compliance
    input_mapping:
      invoice_data: "$.input.invoice_data"
      category: "$.steps.categorize.output.category"
  
  - id: record
    skill_id: suggest-accounting-entry
    input_mapping:
      invoice_data: "$.input.invoice_data"
      validation: "$.steps.validate.output"
      category: "$.steps.categorize.output.category"
      compliance: "$.steps.check-compliance.output"

output:
  summary: "$.steps.record.output"
  validation_status: "$.steps.validate.output.status"
  compliance_status: "$.steps.check-compliance.output.status"
```

## 5. Workflow Lifecycle

1. **Load** — Workflow Runner loads Workflow definition from Domain Pack.
2. **Initialize** — Create Workflow-level context. Validate input against first step's requirements.
3. **Execute Steps** — For each step in order:
   a. Resolve `input_mapping` — map outputs from previous steps (and Workflow input) to current step's inputs.
   b. Call Skill Executor with `skill_id` and resolved inputs.
   c. Store step result in Workflow context.
   d. If step fails, Workflow fails with the step's error.
4. **Finalize** — Resolve Workflow-level `output` from step results.
5. **Record** — Record Workflow-level execution history (with references to each step's execution record).
6. **Return** — Return final output.

## 6. Input Mapping

Input mapping uses a simple JSON path syntax:

| Pattern | Meaning |
|---------|---------|
| `$.input.field_name` | Read from Workflow input parameters |
| `$.steps.step_id.output` | Read from a previous step's output |

In V1, only direct value mapping is supported. No transformations, no conditional mappings, no loops.

## 7. V1 Constraints

- Sequential execution only. Step N+1 starts after Step N completes.
- No branching (if/else, switch).
- No parallel execution.
- No loop/iteration.
- No error handlers (step failure = Workflow failure).
- No timers, subflows, or approval gates.
- Two Workflow Templates per Domain Pack maximum.

## 8. V2+ Evolution

V2 Workflows will add:
- Conditional branching (if/else).
- Parallel Skill execution.
- Human approval gates between steps.
- Error handlers (retry, skip, escalate).
- Custom Workflow authoring.
- Visual Workflow builder (Playground canvas).

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
