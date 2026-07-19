# ADR-0003: AI Provider Abstraction

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

HiveOS executes AI-powered Skills. The choice of AI model provider (local vs cloud, Ollama vs OpenAI) should not be coupled to the Core. Customers need the flexibility to choose providers based on cost, quality, privacy, and infrastructure requirements.

## Decision

The Core defines an AI Provider interface. All Skill execution communicates through this interface. Provider adapters implement the interface for each provider. The Skill Executor never calls a specific provider directly.

V1 ships two adapters: one local (Ollama/LM Studio, primary target) and one cloud (OpenAI-compatible, configurable option).

## Rationale

- Decouples Core from vendor-specific AI models.
- Enables on-premise-first (local models default) while allowing cloud AI as an upgrade path.
- Adding new providers (Claude, Gemini, custom) does not require Core changes.
- The AI Provider is a thin invocation layer — it receives a compiled prompt, not internal system state.

## Consequences

- Positive: Vendor lock-in protection. Providers can be swapped via configuration.
- Positive: On-premise deployment works without any external AI dependency.
- Negative: Must build and maintain at least two adapter implementations.
- Negative: Interface design must be general enough to accommodate different provider APIs.

## References

- Product Decisions: PD-03
- AI Provider Specification
- Runtime Architecture §3 (Skill execution)
- Product Principles P6 (On-Premise First), P7 (Extensibility)
