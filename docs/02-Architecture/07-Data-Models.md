# 07 — Data Models

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Complete (Phase 1)  
> **Last Updated:** 2026-07-24  
> **Upstream Sources:** `docs/ADR/0011`, `docs/01-Product/09`–`14`  
> **Dependencies:** 05-Core-Services (interface definitions reference these models)  
> **Priority:** 5  

---

## Table of Contents

1. [Schema Conventions](#1-schema-conventions)
2. [ExecutionContext](#2-executioncontext)
3. [ExecutionRecord](#3-executionrecord)
4. [SkillDefinition](#4-skilldefinition)
5. [WorkflowDefinition](#5-workflowdefinition)
6. [DomainPackMetadata](#6-domainpackmetadata)
7. [KnowledgeDocument](#7-knowledgedocument)
8. [CapabilityResult](#8-capabilityresult)
9. [CapabilityInfo](#9-capabilityinfo)
10. [AIProviderResponse](#10-aiproviderresponse)
11. [ProviderCapabilities](#11-providervcapabilities)
12. [ErrorEnvelope](#12-errorenvelope)
13. [KnowledgeSearchRequest](#13-knowledgesearchrequest)
14. [KnowledgeSearchResponse](#14-knowledgesearchresponse)
15. [HealthStatus](#15-healthstatus)
16. [Cross-References](#16-cross-references)

---

## 1. Schema Conventions

### 1.1 Format

All schemas follow **JSON Schema Draft 2020-12** syntax. Schemas are defined in YAML for readability within this document; the canonical version is JSON Schema.

### 1.2 Naming Convention

| Category | Pattern | Example |
|----------|---------|---------|
| Model types | `PascalCase` | `ExecutionContext`, `SkillDefinition` |
| Fields | `snake_case` | `skill_id`, `input_parameters` |
| IDs | `string` (UUID v4 or qualified ID) | `"a1b2c3d4-..."`, `"accounting/validate-invoice"` |
| Error codes | `UPPER_SNAKE_CASE` | `INPUT_VALIDATION_FAILED` |
| Enums | `lower_snake_case` | `"running"`, `"completed"`, `"failed"` |

### 1.3 Required vs Optional

- **Required:** Fields that must always be present. Listed explicitly in each schema's `required` array.
- **Optional:** Fields that MAY be absent (typically conditional on execution phase or data availability). Represented by omitting from `required`.
- **Nullable:** Fields that are always present but MAY be `null`. Represented by `nullable: true`.

### 1.4 Schema Versioning

Each major schema carries a `schema_version` integer field. Versions are independent per schema:

| Convention | Rule |
|-----------|------|
| Major version | Increment when fields are added, removed, renamed, or change type |
| Minor version | Increment when constraints change (new enum value, wider range) |
| Backward compatibility | Readers MUST accept any version ≥ their own. Unknown fields ignored. |

For ExecutionContext and ExecutionRecord, `schema_version: 1` is the initial deployment. Incremented per the rules above.

### 1.5 Extensibility

- `additionalProperties: true` on most models — services MAY add provider-specific fields.
- Services MUST NOT require fields outside the schema definition.
- Extra fields are preserved through the system but not validated.

### 1.6 ID Generation

- UUIDs: `uuid4` hex string with hyphens (`550e8400-e29b-41d4-a716-446655440000`).
- Domain Pack IDs, Skill IDs, Workflow IDs: lower-kebab-case, dot-qualified (`accounting.validate-invoice`).
- All IDs are case-sensitive.

---

## 2. ExecutionContext

The complete state container for a single Skill or Workflow execution. Single source of truth (ADR-0011).

```yaml
schema_version: 1
description: |
  Complete state container for one Skill or Workflow execution.
  Populated sequentially through execution phases. Persisted by
  Execution History Service at the end of execution.
type: object
required:
  - schema_version
  - id
  - type
  - status
  - timestamps
  - input_parameters
  - errors
properties:
  schema_version:
    type: integer
    description: Schema version for forward compatibility
    minimum: 1
    default: 1

  id:
    type: string
    format: uuid
    description: Unique execution identifier (uuid4)
    example: "550e8400-e29b-41d4-a716-446655440000"

  type:
    type: string
    enum: ["skill", "workflow"]
    description: Type of execution

  skill_id:
    type: string
    description: Qualified Skill ID being executed
    example: "accounting/validate-invoice"
    nullable: true

  workflow_id:
    type: string
    description: Qualified Workflow ID (Workflow executions only)
    example: "accounting/invoice-processing"
    nullable: true

  parent_execution_id:
    type: string
    format: uuid
    description: Parent execution ID (for Workflow → Skill tracing)
    nullable: true

  status:
    type: string
    enum: ["running", "completed", "failed"]
    description: Current execution status
    default: "running"

  timestamps:
    type: object
    description: Key timestamps throughout the execution lifecycle
    required:
      - started
    properties:
      started:
        type: string
        format: date-time
        description: Execution start time (ISO 8601)
      knowledge_retrieved:
        type: string
        format: date-time
        description: When knowledge retrieval completed
        nullable: true
      ai_invoked:
        type: string
        format: date-time
        description: When AI provider was called
        nullable: true
      completed:
        type: string
        format: date-time
        description: Execution completion time
        nullable: true

  input_parameters:
    type: object
    description: User-provided input parameters (validated against Skill's input_schema)
    additionalProperties: true
    default: {}

  knowledge_retrieved:
    type: array
    description: Documents retrieved during knowledge retrieval phase
    items:
      type: object
      properties:
        source:
          type: string
          description: Source tag (domain: or org: prefix)
        title:
          type: string
          description: Document title
        content:
          type: string
          description: Document content (may be truncated or reference-only)
        relevance_score:
          type: number
          minimum: 0
          maximum: 1
          description: Relevance score from search index
      required:
        - source
        - title
    default: []

  capability_results:
    type: object
    description: Results from capability invocations, keyed by capability_id
    additionalProperties:
      "$ref": "#/definitions/CapabilityResult"
    default: {}

  prompt_sent:
    type: string
    description: Complete compiled prompt sent to AI Provider
    nullable: true

  ai_response:
    type: object
    description: Response from AI Provider invocation
    properties:
      content:
        type: string
        description: Generated response text
      model_used:
        type: string
        description: Actual model that generated the response
      usage:
        type: object
        description: Token usage statistics
        properties:
          prompt_tokens:
            type: integer
            minimum: 0
          completion_tokens:
            type: integer
            minimum: 0
          total_tokens:
            type: integer
            minimum: 0
      duration_ms:
        type: integer
        minimum: 0
        description: Time taken by AI provider
      error:
        type: string
        description: Error message if invocation failed
        nullable: true
    required:
      - content
    nullable: true

  output:
    type: object
    description: Validated output matching the Skill's output_schema
    additionalProperties: true
    nullable: true

  errors:
    type: array
    description: Errors encountered during execution
    items:
      "$ref": "#/definitions/ErrorEnvelope"
    default: []

  steps:
    type: object
    description: Step results (Workflow executions only). Keyed by step ID.
    additionalProperties:
      type: object
      properties:
        output:
          type: object
          additionalProperties: true
          description: Output from the step's Skill execution
        status:
          type: string
          enum: ["completed", "failed"]
          description: Step execution status
        skill_execution_id:
          type: string
          format: uuid
          description: The Skill-level ExecutionContext ID for this step
      required:
        - status
        - skill_execution_id
    default: {}

  # V2+ placeholder fields
  user_feedback:
    type: object
    nullable: true
    default: null
```

---

## 3. ExecutionRecord

The immutable record persisted by Execution History Service. Contains the complete Execution Context at the time of persistence.

```yaml
schema_version: 1
description: |
  Immutable execution record persisted by Execution History Service.
  Contains complete Execution Context snapshot. Records are never
  modified after creation (append-only).
type: object
required:
  - schema_version
  - id
  - type
  - skill_id
  - domain_pack_id
  - started_at
  - completed_at
  - duration_ms
  - status
  - errors
properties:
  schema_version:
    type: integer
    minimum: 1
    default: 1

  id:
    type: string
    format: uuid
    description: Unique record identifier (matches ExecutionContext.id)

  type:
    type: string
    enum: ["skill", "workflow"]

  skill_id:
    type: string
    description: Qualified Skill ID
    nullable: true

  workflow_id:
    type: string
    description: Qualified Workflow ID (Workflow executions only)
    nullable: true

  domain_pack_id:
    type: string
    description: Domain Pack that owns the Skill/Workflow
    example: "accounting"

  started_at:
    type: string
    format: date-time
    description: When execution started

  completed_at:
    type: string
    format: date-time
    description: When execution completed

  duration_ms:
    type: integer
    minimum: 0
    description: Total execution duration in milliseconds

  ai_provider:
    type: string
    description: AI provider used (e.g., "local", "openai")
    nullable: true

  model_used:
    type: string
    description: AI model used (e.g., "llama3.1", "gpt-4o-mini")
    nullable: true

  prompt_version:
    type: string
    description: Version identifier for the compiled prompt
    nullable: true

  input_parameters:
    type: object
    additionalProperties: true
    description: User-provided input parameters

  output:
    type: object
    additionalProperties: true
    description: Final validated output
    nullable: true

  status:
    type: string
    enum: ["completed", "failed"]

  knowledge_retrieved:
    type: array
    description: Knowledge documents retrieved (references with scores)
    items:
      type: object
      properties:
        source:
          type: string
        title:
          type: string
        relevance_score:
          type: number
          minimum: 0
          maximum: 1
      required:
        - source

  prompt_sent:
    type: string
    description: The compiled prompt (full text)
    nullable: true

  ai_response:
    type: string
    description: Raw AI response text
    nullable: true

  capability_results:
    type: object
    additionalProperties:
      "$ref": "#/definitions/CapabilityResult"
    description: Results from capability invocations
    default: {}

  errors:
    type: array
    items:
      "$ref": "#/definitions/ErrorEnvelope"
    description: Errors encountered during execution
    default: []

  parent_execution_id:
    type: string
    format: uuid
    description: Parent execution ID (Workflow → Skill tracing)
    nullable: true

  user_feedback:
    type: object
    nullable: true
    default: null
    description: User feedback on this execution (V2+)
```

**Indexes (Execution History Service SQLite):**

| Column | Indexed | Purpose |
|--------|---------|---------|
| `id` | Primary key | Direct record lookup |
| `skill_id` | Yes | Filter by Skill |
| `workflow_id` | Yes | Filter by Workflow |
| `domain_pack_id` | Yes | Filter by Domain Pack |
| `status` | Yes | Filter by completion status |
| `started_at` | Yes | Date range queries |
| `type` | Yes | Filter by execution type |

---

## 4. SkillDefinition

The parsed definition of a Skill, loaded from Skill YAML in the Domain Pack.

```yaml
schema_version: 1
description: |
  Parsed Skill definition from Domain Pack Skill YAML. Defines what the
  Skill does, its inputs/outputs, required context, and AI configuration.
type: object
required:
  - id
  - name
  - version
  - input_schema
  - output_schema
  - knowledge_requirements
  - required_capabilities
  - instruction
  - model
properties:
  id:
    type: string
    description: Unique Skill identifier (qualified, lower-kebab-case)
    pattern: "^[a-z][a-z0-9-]+(/[a-z][a-z0-9-]+)?$"
    example: "accounting/validate-invoice"

  name:
    type: string
    description: Human-readable Skill name
    example: "Validate Invoice"

  description:
    type: string
    description: Brief description of what this Skill does
    nullable: true

  version:
    type: string
    pattern: "^\\d+\\.\\d+\\.\\d+$"
    description: Semantic version
    example: "1.0.0"

  input_schema:
    type: object
    description: JSON Schema for validation of input parameters
    properties:
      type:
        type: string
        default: "object"
      properties:
        type: object
        additionalProperties:
          type: object
          description: Field definition
          properties:
            type:
              type: string
            description:
              type: string
      required:
        type: array
        items:
          type: string
      additionalProperties:
        type: boolean
        default: false

  output_schema:
    type: object
    description: JSON Schema for validation of the AI output
    $ref: "#/definitions/input_schema/properties"  # Same structure as input_schema

  knowledge_requirements:
    type: object
    description: Declares what knowledge the Skill needs
    properties:
      tags:
        type: array
        items:
          type: string
        description: Knowledge tags to search for
        example: ["invoice_validation", "tax_rules"]
      concepts:
        type: array
        items:
          type: string
        description: Domain concepts referenced by the Skill
        example: ["tax_rate", "verification_threshold"]
    required:
      - tags

  required_capabilities:
    type: array
    items:
      type: string
    description: |
      List of capability IDs required for this Skill execution.
      Validated by Capability Service at runtime.
    example: ["knowledge_search", "calculator"]
    minItems: 0
    default: []

  model:
    type: object
    description: AI model configuration for this Skill
    properties:
      provider:
        type: string
        default: "default"
        description: AI provider selection. "default" = use global config.
      temperature:
        type: number
        minimum: 0
        maximum: 2
        default: 0.3
      max_tokens:
        type: integer
        minimum: 1
        maximum: 32768
        default: 2048
    required:
      - provider

  instruction:
    type: string
    description: |
      Embedded AI prompt template (ADR-0009). Uses placeholders:
      {{knowledge}}, {{input}}, {{capabilities}} for runtime interpolation.
    example: |
      You are an invoice validation assistant.
      Review the following invoice data:
      {{input}}

      Use this context:
      {{knowledge}}

      Tool results:
      {{capabilities}}

  timeout_seconds:
    type: integer
    minimum: 1
    maximum: 600
    default: 120
    description: Per-execution timeout for this specific Skill
```

---

## 5. WorkflowDefinition

The parsed definition of a Workflow Template, loaded from Workflow YAML in the Domain Pack.

```yaml
schema_version: 1
description: |
  Parsed Workflow Template definition. V1 Workflows are sequential
  Skill pipelines. No branching, no parallel steps, no error handlers.
type: object
required:
  - id
  - name
  - version
  - steps
properties:
  id:
    type: string
    description: Unique Workflow identifier (qualified, lower-kebab-case)
    pattern: "^[a-z][a-z0-9-]+(/[a-z][a-z0-9-]+)?$"
    example: "accounting/invoice-processing"

  name:
    type: string
    description: Human-readable Workflow name
    example: "Invoice Processing Workflow"

  description:
    type: string
    nullable: true

  version:
    type: string
    pattern: "^\\d+\\.\\d+\\.\\d+$"
    example: "1.0.0"

  steps:
    type: array
    description: Ordered list of Workflow steps
    items:
      type: object
      required:
        - id
        - skill_id
      properties:
        id:
          type: string
          description: Step identifier (unique within this Workflow)
          pattern: "^[a-z][a-z0-9-]+$"
          example: "validate"
        skill_id:
          type: string
          description: Qualified Skill ID to execute for this step
          example: "accounting/validate-invoice"
        input_mapping:
          type: object
          description: |
            Maps workflow inputs and previous step outputs to this
            step's input parameters. Uses JSON path expressions.
          additionalProperties:
            type: string
            description: JSON path expression
            example: "$.input.invoice_data"
          default: {}
        on_error:
          type: string
          enum: ["fail"]
          description: |
            Error handling for this step. V1 only supports "fail"
            (step failure → workflow failure). Future values:
            "skip", "use_default", custom error handlers.
          default: "fail"

  output_mapping:
    type: object
    description: |
      Maps step outputs to the final Workflow output.
      Keys are output field names, values are JSON path expressions.
    additionalProperties:
      type: string
      description: JSON path expression
      example: "$.steps.validate.output"
    default: {}
```

---

## 6. DomainPackMetadata

Metadata for an installed Domain Pack.

```yaml
schema_version: 1
description: |
  Metadata for a Domain Pack. Populated from domain.yaml manifest.
  Used by Domain Pack Manager for lifecycle operations.
type: object
required:
  - id
  - version
  - name
  - description
  - min_core_version
  - skills
  - status
properties:
  id:
    type: string
    description: Globally unique Domain Pack identifier (lower-kebab-case)
    pattern: "^[a-z][a-z0-9-]+$"
    example: "accounting"

  version:
    type: string
    pattern: "^\\d+\\.\\d+\\.\\d+$"
    description: Current installed version

  name:
    type: string
    description: Human-readable pack name
    example: "Accounting Domain Pack"

  description:
    type: string
    nullable: true

  min_core_version:
    type: string
    pattern: "^\\d+\\.\\d+\\.\\d+$"
    description: Minimum HiveOS Core version required

  author:
    type: object
    description: Pack author information
    properties:
      name:
        type: string
      url:
        type: string
        format: uri
        nullable: true

  skills:
    type: array
    description: List of Skill IDs defined in this pack
    items:
      type: object
      required:
        - id
      properties:
        id:
          type: string
    default: []

  workflows:
    type: array
    description: List of Workflow Template IDs defined in this pack
    items:
      type: object
      properties:
        id:
          type: string
    default: []

  status:
    type: string
    enum: ["active", "disabled"]
    description: Current lifecycle status
    default: "active"

  installed_at:
    type: string
    format: date-time
    description: When the pack was installed
    nullable: true

  install_path:
    type: string
    description: Absolute path to the installed pack directory
    nullable: true
```

---

## 7. KnowledgeDocument

A single knowledge document stored in the unified search index (ADR-0007).

```yaml
schema_version: 1
description: |
  A knowledge document in the unified search index. Source-tagged
  to distinguish Domain Knowledge from Organization Knowledge.
type: object
required:
  - id
  - source_type
  - source_id
  - content
  - format
  - tags
properties:
  id:
    type: string
    format: uuid
    description: Unique document identifier

  source_type:
    type: string
    enum: ["domain", "org"]
    description: |
      Source of the knowledge. "domain" = from Domain Pack (read-only).
      "org" = customer Organization Knowledge (mutable).

  source_id:
    type: string
    description: |
      Origin identifier. For domain: pack_id + relative path.
      For org: ingestion batch ID + filename.
    example: "accounting/knowledge/01-accounting-principles.md"

  title:
    type: string
    description: Document title (from frontmatter or filename)
    nullable: true

  content:
    type: string
    description: Full document content (may be truncated at storage)

  format:
    type: string
    enum: ["markdown", "text", "pdf_text"]
    description: Source document format

  tags:
    type: array
    items:
      type: string
    description: Knowledge tags for search and filtering
    example: ["invoice_validation", "tax_rules"]

  metadata:
    type: object
    description: Arbitrary metadata (source-specific)
    additionalProperties: true
    default: {}

  immutable:
    type: boolean
    description: |
      true = Domain Knowledge (read-only, cannot be modified by customer).
      false = Organization Knowledge (customer-owned, mutable).
    default: false

  created_at:
    type: string
    format: date-time
    description: When this document was indexed
    nullable: true
```

---

## 8. CapabilityResult

Result from invoking a single capability through the Capability Service.

```yaml
schema_version: 1
description: |
  Result from a single capability invocation. Stored in
  ExecutionContext.capability_results.
type: object
required:
  - capability_id
  - input
  - output
  - duration_ms
properties:
  capability_id:
    type: string
    description: Capability identifier
    example: "knowledge_search"

  input:
    type: object
    description: The input parameters passed to the capability
    additionalProperties: true

  output:
    type: object
    description: The output returned by the capability
    additionalProperties: true
    nullable: true

  duration_ms:
    type: integer
    minimum: 0
    description: Time taken by the capability invocation

  error:
    type: string
    description: Error message if the capability failed
    nullable: true
```

---

## 9. CapabilityInfo

Registration information for a capability in the Capability Service registry.

```yaml
schema_version: 1
description: |
  Capability registration metadata. Used for capability discovery
  and runtime validation of Skill required_capabilities.
type: object
required:
  - id
  - name
  - synchronous
  - timeout_seconds
properties:
  id:
    type: string
    description: Capability identifier (lower-kebab-case)
    example: "knowledge_search"

  name:
    type: string
    description: Human-readable capability name
    example: "Knowledge Search"

  description:
    type: string
    nullable: true

  input_schema:
    type: object
    description: Expected input structure (JSON Schema)
    additionalProperties: true
    nullable: true

  output_schema:
    type: object
    description: Guaranteed output structure (JSON Schema)
    additionalProperties: true
    nullable: true

  synchronous:
    type: boolean
    description: true = blocking execution, false = returns job ID
    default: true

  timeout_seconds:
    type: integer
    minimum: 1
    maximum: 300
    description: Maximum execution time before timeout
    default: 30
```

---

## 10. AIProviderResponse

Response from an AI Provider invocation.

```yaml
schema_version: 1
description: |
  Response from AI Provider Service. Wraps the generated content
  with metadata about tokens, model, and execution time.
type: object
required:
  - content
  - model_used
  - usage
  - duration_ms
properties:
  content:
    type: string
    description: Generated response text from the AI model
    example: "{\"status\": \"valid\", \"confidence\": 0.95, ...}"

  model_used:
    type: string
    description: Actual model that generated the response
    example: "llama3.1:8b"

  usage:
    type: object
    description: Token usage statistics
    required:
      - prompt_tokens
      - completion_tokens
      - total_tokens
    properties:
      prompt_tokens:
        type: integer
        minimum: 0
      completion_tokens:
        type: integer
        minimum: 0
      total_tokens:
        type: integer
        minimum: 0

  duration_ms:
    type: integer
    minimum: 0
    description: Time taken by the AI provider invocation

  error:
    type: string
    description: Error message if invocation failed
    nullable: true
```

---

## 11. ProviderCapabilities

Capability declaration for an AI Provider adapter. Describes what the provider supports.

```yaml
schema_version: 1
description: |
  Capability declaration for an AI Provider adapter. Informs the
  Skill Executor what features the provider supports.
type: object
properties:
  provider_name:
    type: string
    description: Provider adapter name
    example: "ollama"

  supports_streaming:
    type: boolean
    description: Whether the provider supports token-by-token streaming
    default: false

  supports_tools:
    type: boolean
    description: Whether the provider supports function/tool calling
    default: false

  supports_multimodal:
    type: boolean
    description: Whether the provider supports image/video input
    default: false

  max_context_tokens:
    type: integer
    description: Maximum context window size in tokens
    minimum: 1
    default: 4096

  supported_models:
    type: array
    items:
      type: string
    description: List of model identifiers available through this provider
    default: []
```

---

## 12. ErrorEnvelope

Standard error format used across all services.

```yaml
schema_version: 1
description: |
  Standard error envelope used across all HiveOS services.
  Every error in the system conforms to this structure.
type: object
required:
  - code
  - message
properties:
  code:
    type: string
    description: Unique error code (UPPER_SNAKE_CASE)
    example: "INPUT_VALIDATION_FAILED"

  message:
    type: string
    description: Human-readable error description
    example: "Missing required field: invoice_data"

  details:
    type: object
    description: Additional error context (field names, expected values, etc.)
    additionalProperties: true
    default: {}

  transient:
    type: boolean
    description: |
      true = error may resolve on retry (network timeout, rate limit).
      false = error is deterministic (schema violation, missing resource).
    default: false

  trace_id:
    type: string
    description: Correlation ID for this error (ExecutionContext.id)
    nullable: true
```

**Standard Error Codes:**

| Code | Meaning | Transient | Source |
|------|---------|-----------|--------|
| `SKILL_NOT_FOUND` | Requested skill_id not installed | No | Skill Executor |
| `SKILL_INVALID` | Skill YAML malformed or missing fields | No | Skill Executor |
| `INPUT_VALIDATION_FAILED` | Input doesn't match input_schema | No | Skill Executor |
| `KNOWLEDGE_RETRIEVAL_FAILED` | Knowledge Service unavailable | Yes | Skill Executor |
| `KNOWLEDGE_TIMEOUT` | Knowledge retrieval exceeded timeout | Yes | Skill Executor |
| `CAPABILITY_NOT_REGISTERED` | Required capability not found | No | Skill Executor |
| `CAPABILITY_EXECUTION_FAILED` | Capability returned error | Depends | Skill Executor |
| `CAPABILITY_TIMEOUT` | Capability exceeded timeout | Yes | Skill Executor |
| `PROMPT_COMPILATION_FAILED` | Prompt template malformed | No | Skill Executor |
| `AI_PROVIDER_FAILED` | AI provider returned error | Yes | AI Provider |
| `AI_PROVIDER_TIMEOUT` | AI provider exceeded timeout | Yes | AI Provider |
| `OUTPUT_PARSE_FAILED` | AI response not valid JSON | No | Skill Executor |
| `OUTPUT_VALIDATION_FAILED` | Output doesn't match output_schema | No | Skill Executor |
| `EXECUTION_TIMEOUT` | Total execution exceeded timeout | No | Skill Executor |
| `HISTORY_RECORDING_FAILED` | Execution History write failed | Yes | Execution History |
| `WORKFLOW_NOT_FOUND` | Requested workflow_id not installed | No | Workflow Runner |
| `WORKFLOW_INVALID` | Workflow YAML malformed | No | Workflow Runner |
| `INPUT_MAPPING_RESOLVED_TO_NULL` | JSON path referenced non-existent data | No | Workflow Runner |
| `PACK_NOT_FOUND` | Domain Pack not installed | No | Domain Pack Manager |
| `PACK_INVALID` | domain.yaml malformed | No | Domain Pack Manager |
| `PACK_VERSION_MISMATCH` | min_core_version > current Core version | No | Domain Pack Manager |

---

## 13. KnowledgeSearchRequest

Request parameters for searching the unified knowledge index.

```yaml
schema_version: 1
description: |
  Request parameters for Knowledge Service search.
  Keyword + tag-based search (no vector embeddings in V1).
type: object
required:
  - query
properties:
  query:
    type: string
    description: Free-text search query
    minLength: 1
    maxLength: 500

  tags:
    type: array
    items:
      type: string
    description: Filter by knowledge tags
    default: []

  source_type:
    type: string
    enum: ["domain", "org"]
    description: Filter by knowledge source (omit for both)
    nullable: true
    default: null

  limit:
    type: integer
    minimum: 1
    maximum: 50
    default: 10
    description: Maximum number of results to return

  offset:
    type: integer
    minimum: 0
    default: 0
    description: Result offset for pagination
```

---

## 14. KnowledgeSearchResponse

Response from a knowledge search operation.

```yaml
schema_version: 1
description: |
  Response wrapper for knowledge search results.
type: object
required:
  - results
  - total_count
properties:
  results:
    type: array
    description: Search result documents
    items:
      "$ref": "#/definitions/KnowledgeDocument"
    default: []

  total_count:
    type: integer
    minimum: 0
    description: Total number of matching documents (before limit)

  query:
    type: string
    description: Original search query (echoed for debugging)
```

---

## 15. HealthStatus

Standard health check response. Every service implements `/health` (A6).

```yaml
schema_version: 1
description: |
  Standard health check response. Every Core service implements
  a /health endpoint returning this structure.
type: object
required:
  - status
  - version
  - uptime_seconds
properties:
  status:
    type: string
    enum: ["healthy", "degraded", "unhealthy"]
    description: Overall service health

  version:
    type: string
    description: Service version
    example: "1.0.0"

  uptime_seconds:
    type: integer
    minimum: 0
    description: Seconds since service started

  dependencies:
    type: array
    description: Health status of downstream dependencies
    items:
      type: object
      properties:
        name:
          type: string
          description: Dependency name
        status:
          type: string
          enum: ["healthy", "unhealthy", "not_checked"]
        message:
          type: string
          nullable: true
      required:
        - name
        - status
    default: []
```

---

## 16. Cross-References

| Target | Relationship |
|--------|-------------|
| 03-Runtime-Execution | Execution Context lifecycle uses these models |
| 04-Domain-Pack-Specification | Skill/Workflow/Knowledge schemas referenced as format specs |
| 05-Core-Services | All service interfaces reference these models as input/output |
| 06-API-Reference | API request/response bodies composed from these models |
| 08-Contracts | ErrorEnvelope, naming conventions, versioning strategy |
| docs/ADR/0011 | Execution Context object (motivating this schema) |
| docs/ADR/0007 | KnowledgeDocument source tagging (domain:/org:) |
| docs/01-Product/09-Domain-Pack-Specification.md | Domain Pack format (upstream) |
| docs/01-Product/13-Skill-Specification.md | Skill format (upstream) |
| docs/01-Product/14-Workflow-Specification.md | Workflow format (upstream) |

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
| 1.1.0 | 2026-07-24 | Principal Software Architect | Complete JSON Schema definitions for all 14 models |
