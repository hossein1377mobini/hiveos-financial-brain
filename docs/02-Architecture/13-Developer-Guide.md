# 13 — Developer Guide

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Dependencies:** All preceding documents  
> **Priority:** 8  

---

## Purpose

Setup, build, test, and contribute guide. A new developer reads this to go from zero to running HiveOS locally, understanding the codebase structure, and making their first contribution.

## Scope

**In:** Prerequisites, clone and setup, configuration, running locally, running tests, code style, PR workflow, how to create a Domain Pack, how to add a Capability, how to add an AI Provider adapter.

**Out:** Detailed codebase structure (generated from code), API documentation (06-API-Reference).

## Table of Contents

```
1. Prerequisites
   1.1 Python 3.11+
   1.2 uv (package manager)
   1.3 Docker (for running services)
   1.4 Git

2. Getting Started
   2.1 Clone Repository
   2.2 Install Dependencies
   2.3 Configuration (copy config template)
   2.4 Run HiveOS (development mode)
   2.5 Verify (health check)

3. Codebase Structure
   3.1 Directory Layout
   3.2 Core Services Locations
   3.3 Tests Locations
   3.4 Documentation Locations

4. Running Tests
   4.1 Unit Tests
   4.2 Integration Tests
   4.3 End-to-End Tests
   4.4 Test Fixtures

5. Code Style
   5.1 Python (PEP 8)
   5.2 YAML Conventions
   5.3 Commit Message Format
   5.4 PR Checklist

6. Contribution Workflow
   6.1 Branch Naming
   6.2 PR Template
   6.3 Review Process
   6.4 ADR Requirement (for architecture-changing PRs)

7. Domain Pack Development
   7.1 Creating a Pack (tutorial)
   7.2 Writing Skill Definitions
   7.3 Writing Workflow Templates
   7.4 Testing a Pack

8. Adding a Capability
   8.1 Capability Interface
   8.2 Registration
   8.3 Testing

9. Adding an AI Provider Adapter
   9.1 Provider Interface
   9.2 ProviderCapabilities
   9.3 Testing with Real and Mock Providers
```

## Estimated Size

~800 lines

## Cross-References

| Target | Relationship |
|--------|-------------|
| 04-Domain-Pack-Specification | Tutorial for creating packs references this format |
| 05-Core-Services | Capability and Provider interfaces defined here |
| 14-Testing | Test strategy, infra details |

## Document Boundary Verification

This document defines DEVELOPMENT WORKFLOW (how to contribute). It does NOT define what to build (all other docs). Process vs specification: zero overlap.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
