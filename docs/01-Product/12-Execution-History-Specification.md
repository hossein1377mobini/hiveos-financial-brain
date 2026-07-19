# Execution History Specification

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Runtime Architecture (08), ADR-0002

---

## 1. Purpose

The Execution History Service records every Skill and Workflow execution with full context. In V1, this serves debugging and audit purposes. In V2+, it becomes the foundation for pattern detection, recommendation engine, and learning capabilities.

Execution History is NOT learning. It is structured, immutable data collection. Learning (pattern detection, recommendation, confidence scoring) is built on top of this data in V2.

## 2. What Is Recorded

Every execution record contains the full Execution Context:

```yaml
execution_record:
  id: uuid
  type: "skill" | "workflow"
  skill_id: string
  workflow_id: string (optional)
  domain_pack_id: string
  
  # Timing
  started_at: iso8601
  completed_at: iso8601
  duration_ms: integer
  
  # AI Provider
  ai_provider: string
  model_used: string
  prompt_version: string (optional)
  
  # Inputs & Outputs
  input_parameters: {}         # User-provided inputs
  output: {}                   # Final validated output
  status: "completed" | "failed"
  
  # Knowledge
  knowledge_retrieved:         # Documents retrieved during execution
    - source: string
      title: string
      relevance_score: float
  
  # Audit Trail
  prompt_sent: string          # The compiled prompt
  ai_response: string          # Raw AI response
  capability_results: {}       # Results from capability invocations
  errors: []                   # Any errors encountered
  
  # User Feedback (V2+)
  user_feedback: null
  
  # Relationships
  parent_execution_id: string (optional)  # For Workflow → Skill tracing
```

## 3. Storage Model

- Execution History is append-only. Records are never modified after creation.
- Stored in persistent storage (local database/file) on customer infrastructure.
- Indexed by: `id`, `skill_id`, `workflow_id`, `domain_pack_id`, `status`, `started_at`.
- Retention: unlimited in V1 (storage permitting). Configurable in V2.

## 4. How Records Are Created

1. Skill Executor creates Execution Context at start of execution.
2. Skill Executor populates Execution Context throughout the lifecycle.
3. On completion (success or failure), Skill Executor sends full Execution Context to Execution History Service.
4. Execution History Service persists the record immutably.
5. Execution History Service returns a confirmation with the record ID.

## 5. API (Internal)

```
record_execution(context: ExecutionContext) -> record_id: string
get_execution(record_id: string) -> ExecutionRecord
query_executions(filters: {skill_id?, status?, date_from?, date_to?}) -> ExecutionRecord[]
```

## 6. V1 Use Cases

- **Debugging:** View full execution details for any Skill or Workflow run.
- **Audit:** Prove what happened, when, with what inputs and outputs.
- **Playground:** Developer inspects prompts, responses, and knowledge retrieval for Skill debugging.
- **Support:** Customer support can investigate failed executions with full context.

## 7. V2+ Use Cases (Foundation)

- **Pattern detection:** Analyze execution records to find recurring sequences.
- **Recommendation engine:** Surface patterns based on execution frequency, success rate, and user feedback.
- **Learning from rejection:** Correlate rejected patterns with execution history to improve detection.
- **Performance analytics:** Identify slow Skills, failing Workflows, underperforming models.
- **Cost tracking:** Estimate AI provider costs from token usage.

## 8. Design Rules

- Records are immutable. No UPDATE, only INSERT.
- Records are timestamped and ordered.
- Full prompt and response are stored (not just summaries).
- Execution History never calls external services.
- Execution History is always available (offline-compatible).

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
