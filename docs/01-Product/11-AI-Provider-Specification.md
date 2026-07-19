# AI Provider Specification

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** Runtime Architecture (08), Skill Specification (13), ADR-0003

---

## 1. Purpose

The AI Provider abstraction layer decouples the HiveOS Core from specific AI model vendors. The Core defines an interface; provider adapters implement it. The Skill Executor communicates only with the interface, never with a specific provider directly.

## 2. Why an Abstraction?

- **On-premise first:** Local models (Ollama, LM Studio) are the default. No external dependency.
- **Vendor flexibility:** Customers choose the best model for their use case and budget.
- **Future-proofing:** New AI capabilities (multimodal, agentic, reasoning models) can be added via new adapters.
- **Data sovereignty:** Cloud AI is an optional, explicitly configured choice — never the default.

## 3. Provider Interface

```yaml
provider:
  invoke:
    input:
      prompt: string                    # The compiled prompt from Skill Executor
      model_id: string                  # Model identifier (e.g., "llama3.1", "gpt-4o")
      parameters: {}                    # Model-specific parameters (temperature, max_tokens, etc.)
    output:
      content: string                   # Generated response text
      model_used: string                # Actual model that generated the response
      usage:
        prompt_tokens: integer
        completion_tokens: integer
        total_tokens: integer
      duration_ms: integer
      error: string (optional)          # Error message if invocation failed
```

## 4. Provider Adapters (V1)

### Default: Local Model Adapter

| Property | Value |
|----------|-------|
| Implementation | Ollama or LM Studio compatible API |
| Interface | HTTP/REST to local endpoint |
| Default model | Configurable (e.g., llama3.1, qwen2.5) |
| Authentication | None (local) |
| Data flow | All data stays on local machine |
| Status | Primary deployment target |

### Optional: Cloud Model Adapter

| Property | Value |
|----------|-------|
| Implementation | OpenAI-compatible API |
| Interface | HTTP/REST to external endpoint |
| Default model | Configurable (e.g., gpt-4o-mini) |
| Authentication | API key (customer-configured) |
| Data flow | Prompt data sent to external provider |
| Status | Documented configuration option |

## 5. What the AI Provider Does NOT Receive

The AI Provider does NOT receive the entire Skill definition, Domain Pack structure, or internal system state. It receives only:

- A **compiled prompt** (already assembled by the Skill Executor with knowledge context, user inputs, and Skill instruction).
- A **model_id**.
- **Model parameters** (temperature, max tokens, etc.).

This keeps the AI Provider as a thin invocation layer. All orchestration intelligence lives in the Skill Executor.

## 6. Configuration

```yaml
# HiveOS Configuration (set per Business)
ai:
  provider: local                      # "local" or "cloud"
  local:
    endpoint: http://localhost:11434/api/generate
    default_model: llama3.1
  cloud:
    endpoint: https://api.openai.com/v1
    api_key: ""                        # Customer provides
    default_model: gpt-4o-mini
  parameters:
    temperature: 0.3
    max_tokens: 4096
```

## 7. Error Handling

- If the AI Provider fails (connection error, timeout, model not found), the Skill Executor records the error in Execution Context and returns a failure result.
- Automatic retry is NOT implemented in V1 (the user can retry from the UI).
- Provider switching (fallback from failed local to cloud) is NOT implemented in V1.

## 8. V2+ Considerations

- Multi-model routing (different Skills use different models).
- Streaming responses (for real-time UX).
- Token usage tracking and cost estimation.
- Provider health checks and automatic fallback.
- Custom model fine-tuning integration.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
