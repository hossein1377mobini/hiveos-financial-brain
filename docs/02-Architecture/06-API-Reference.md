# 06 — API Reference

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Dependencies:** 05-Core-Services, 07-Data-Models (shared schemas)  
> **Priority:** 5  

---

## Purpose

Complete external HTTP API contracts for HiveOS. Every endpoint, method, path, request/response body, status code, and error condition. An API client developer (Dashboard frontend, CLI tool, integration partner) reads this document exclusively.

## Scope

**In:** All HTTP endpoints exposed by the Core API Gateway, request schemas, response schemas, status codes, authentication header, error response format, pagination convention, rate limiting conventions.

**Out:** Internal service-to-service interfaces (05-Core-Services), implementation details of how endpoints are processed (03, 05).

## Table of Contents

```
1. API Conventions
   1.1 Base URL
   1.2 Authentication Header
   1.3 Content Type
   1.4 Error Response Format (ErrorEnvelope)
   1.5 Pagination
   1.6 Truncation (large field handling)

2. Health
   GET /health

3. Skill Execution
   POST /run/skill
   Parameters: skill_id, input_parameters, optional context

4. Workflow Execution
   POST /run/workflow
   Parameters: workflow_id, input_parameters

5. Execution History
   GET /history/{record_id}
   GET /history?filters={...}&page={n}&limit={n}

6. Knowledge
   POST /knowledge/search
   POST /knowledge/ingest (V1: upload file)

7. Domain Pack Management
   POST /domain/install
   POST /domain/enable/{pack_id}
   POST /domain/disable/{pack_id}
   POST /domain/remove/{pack_id}
   GET /domain/list
   GET /domain/{pack_id}

8. Configuration
   GET /config
   PUT /config
   GET /config/{key}

9. Error Codes
   9.1 Standard HTTP Status Codes
   9.2 Application Error Codes (by domain)
```

## Estimated Size

~1,000 lines

## Cross-References

| Target | Relationship |
|--------|-------------|
| 05-Core-Services | These endpoints wrap Core Service interfaces |
| 07-Data-Models | Request/response bodies use schemas defined in 07 |
| 08-Contracts | Error envelope format from contracts |
| 10-Security | Authentication mechanism |

## Document Boundary Verification

This document defines the EXTERNAL shape of the API (what the Dashboard calls). It does NOT define how services process these requests (05) or internal service interfaces. API contract vs implementation: zero overlap.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
