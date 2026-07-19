# Skill Specification

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Runtime Architecture (08), Capability Layer Specification (10), AI Provider Specification (11), Domain Pack Specification (09), ADR-0005, ADR-0009

---

## 1. Definition

A Skill is the smallest reusable business capability in HiveOS. It performs a specific business task using Knowledge. Skills are the building blocks of organizational automation.

A Skill is always declarative. It defines *what* should happen, not *how*. The Core's Skill Executor compiles the declaration into execution.

## 2. Skill Origins

| Origin | Description | V1 Status |
|--------|-------------|-----------|
| **Domain Pack Skill** | Pre-built Skill shipped inside a Domain Pack | ✅ V1 |
| **Custom Skill** | Created by the organization from validated patterns or authored directly | 🟡 V2+ |

## 3. Skill Definition (YAML)

Every Skill is defined as a single YAML file in the Domain Pack's `skills/` directory.

```yaml
id: validate-invoice                     # Unique within Domain Pack
name: Validate Invoice
description: >
  Validates an incoming invoice against supplier records, tax rules,
  and company policies. Returns validation status and any flags.
version: 1.0.0

# What the Skill needs from the user
input_schema:
  type: object
  properties:
    invoice_data:
      type: object
      description: Raw invoice data (OCR output or manual entry)
    supplier_id:
      type: string
      description: Supplier identifier for verification

# What the Skill produces
output_schema:
  type: object
  properties:
    status:
      type: string
      enum: [valid, suspicious, invalid, requires_review]
    flags:
      type: array
      items: { type: string }
    confidence:
      type: number

# Knowledge this Skill needs access to
knowledge_requirements:
  tags:
    - invoice_validation
    - tax_rules
    - supplier_records
  concepts:
    - tax_rate
    - supplier_category
    - verification_threshold

# System capabilities this Skill requires
required_capabilities:
  - knowledge_search          # Find relevant policies and records
  - calculator                # Compute tax amounts and totals

# AI model configuration
model:
  provider: default                     # Uses Business-configured provider
  temperature: 0.3
  max_tokens: 2048

# Prompt (V1 — embedded)
instruction: >
  You are an invoice validation assistant for an accounting department.
  
  Given the invoice data and supplier information, validate the invoice
  against the following rules from the retrieved knowledge:
  
  1. Verify supplier exists and is active
  2. Check invoice amount against supplier category thresholds
  3. Validate tax calculation matches applicable rates
  4. Flag any missing required fields
  5. Flag any unusually high amounts
  
  Return a structured validation result with status and any flags.
```

## 4. Skill Granularity

A Skill should be:

- **Atomic enough** to be reusable across multiple Workflows.
- **Complex enough** to produce a single meaningful business outcome.
- **Independent** — not requiring another Skill to produce its output (dependencies are Workflow concerns).

Examples of correct granularity:
- `validate-invoice` (not `validate-invoice-and-approve-and-record`)
- `categorize-expense` (not `categorize-expense-then-update-ledger`)
- `check-tax-compliance` (not `run-full-audit`)

## 5. Skill Lifecycle

The Skill Executor handles:

1. **Load** — Read Skill YAML from Domain Pack.
2. **Validate** — Check input against `input_schema`.
3. **Prepare** — Retrieve knowledge, invoke pre-AI capabilities.
4. **Compile** — Build prompt from instruction + inputs + knowledge + capability results.
5. **Execute** — Send compiled request to AI Provider.
6. **Parse** — Validate AI response against `output_schema`.
7. **Record** — Send full Execution Context to Execution History.
8. **Return** — Return validated output.

## 6. AI Interaction Model

The Skill Executor compiles a **complete prompt** and sends it to the AI Provider. The AI Provider does not know about Skills, Domain Packs, or HiveOS internals. It receives:

- A well-formed prompt containing: instruction, user inputs, retrieved knowledge, capability results.
- Model configuration parameters.
- Returns: generated text.

## 7. V2+ Considerations

- Custom Skill authoring by end-users.
- Skill versioning and migration.
- Skill testing and approval workflow.
- Multi-language prompt support (extract prompts to separate asset files).
- Skill composition (a Skill that calls other Skills).
- Streaming AI response for real-time UX.
- Configurable autonomy level per Skill.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
