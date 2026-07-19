# Capability Layer Specification

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Runtime Architecture (08), Skill Specification (13), ADR-0004

---

## 1. Purpose

The Capability Layer is a set of reusable system-level functions owned by the HiveOS Core. Capabilities sit between Knowledge (what the business knows) and Skills (what the system can do). They provide the execution primitives that Skills depend on, without Skills needing to implement these functions themselves.

## 2. Why a Separate Layer?

Without the Capability Layer, Skills would either:
- Duplicate common functionality (every Skill reimplements file reading or search).
- Contain imperative code to call external services (defeating declarative purity).
- Be tightly coupled to specific system implementations.

The Capability Layer solves all three by providing a standard interface to common operations. Skills declare *what they need*; the Core provides *how it's done*.

## 3. Conceptual Position

```
Knowledge ───▶ Capabilities ───▶ Skills ───▶ Workflows
(What we      (System           (Domain      (Business
 know)         functions)        tasks)       processes)
```

## 4. Capability Interface

Every Capability implements:

```yaml
capability_id: string          # Unique identifier
input_schema: {}               # Expected input structure
output_schema: {}              # Guaranteed output structure
synchronous: boolean           # True = blocking, False = returns job_id
timeout_seconds: integer       # Max execution time
```

## 5. Core Capabilities (V1)

| Capability | ID | Purpose | Input | Output |
|------------|-----|---------|-------|--------|
| Knowledge Search | `knowledge_search` | Query unified knowledge index | `query: string`, `filters: {}`, `limit: int` | `results: [{source, title, content, score}]` |
| File Reader | `file_reader` | Read content from ingested files | `path: string`, `format: string` | `content: string` |
| Web Access | `web_access` | HTTP GET request | `url: string`, `headers: {}` | `status: int`, `body: string`, `headers: {}` |
| Calculator | `calculator` | Evaluate arithmetic expressions | `expression: string` | `result: number` |

## 6. Capability Discovery

The Capability Service maintains a registry of all available capabilities. When the Skill Executor loads a Skill definition, it checks the Skill's `required_capabilities` against the registry. If a required capability is not registered, the Skill execution fails with a clear error message.

## 7. How Skills Use Capabilities

Skills do not call Capabilities directly. The Skill definition declares:

```yaml
required_capabilities:
  - knowledge_search
  - file_reader
```

The Skill Executor:
1. Reads the Skill's `required_capabilities`.
2. Looks up each capability in the Capability Service.
3. Invokes them in the required order (pre-AI or post-AI, as specified by the Skill).
4. Passes results into the Execution Context.

## 8. Extending Capabilities (V2+)

New Capabilities can be added to the Core without modifying existing Skills. A Skill that needs a new capability simply declares it in `required_capabilities`. If the capability exists, it works. If not, execution fails with a clear message.

V2 Capabilities to consider:
- `ocr` — Extract text from images/scanned documents
- `translation` — Translate text between languages
- `database_query` — Query connected databases
- `data_store` — Save structured data
- `email_send` — Send email notifications

## 9. Design Rules

- Capabilities are stateless (no persistent state between invocations).
- Capabilities are synchronous in V1 (async/streaming is V2+).
- Capability implementations are replaceable. The interface is the contract.
- Capabilities never access Domain Pack files directly (those are read-only).
- Capabilities log their execution to Execution History.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
