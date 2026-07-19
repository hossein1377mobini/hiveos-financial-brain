# Documentation Constitution

> **Version:** 1.0.0  
> **Owner:** Chief Product Architect  
> **Status:** Approved  
> **Last Updated:** 2026-07-19  
> **References:** All product documents

---

## 1. Purpose

This Constitution defines how the HiveOS product documentation is created, maintained, and governed. The documentation is the product memory. The chat is only the discussion. Every accepted decision must become part of the official documentation.

## 2. Core Rules

### Rule 1: Documentation is the Source of Truth

The files in `docs/01-Product/` are the canonical source for all product definitions. If a conversation produces a decision, that decision must be reflected in the documentation within the same session. Undocumented decisions do not exist.

### Rule 2: Every Document Has a Header

Every document must include:
- Version
- Owner
- Status (Draft / Stable / Approved)
- Last Updated date
- References to related documents
- Change history table

### Rule 3: Every Change Has a Trail

All significant changes to documents must be recorded in the document's change history table. Changes include:
- New versions from product discovery
- ADR-driven changes
- Clarifications and corrections

### Rule 4: No Discussion-Only Decisions

Every architectural discussion must end with one of these actions:
- Update an existing document
- Create a new document
- Create an ADR
- Explicitly reject the proposal

No accepted decision exists only inside chat history.

### Rule 5: One Document, One Concern

Each document addresses one coherent topic. If a discussion spans multiple topics, update multiple documents. Documents should be independently readable.

### Rule 6: Cross-References

Documents must reference each other where concepts overlap. References use relative paths (e.g., `SEE: Skill Specification (13)`). This creates a navigable web of documentation.

### Rule 7: ADRs for Architectural Decisions

Any decision that affects the architecture, scope, or principles of HiveOS must be recorded as an Architecture Decision Record (ADR) in `docs/ADR/`.

ADR template:
```markdown
# ADR-NNNN: Title

**Status:** Proposed | Approved | Deprecated | Superseded
**Date:** YYYY-MM-DD
**Owner:** Name

## Context
What is the issue that motivated this decision?

## Decision
What is the decision?

## Rationale
Why was this decision made?

## Consequences
What becomes easier or more difficult?

## Alternatives Considered
What other options were evaluated and rejected?

## References
Links to related documents.
```

### Rule 8: Backward Compatibility of Definitions

Once a document reaches "Approved" status, changing a definition requires:
1. An ADR explaining the change.
2. Updating the change history in all affected documents.
3. Checking all cross-referencing documents for consistency.

### Rule 9: V1/V2/Long Term Labels

Every feature, concept, or capability must be labeled as:
- **V1** — Must ship in the first release
- **V2** — Planned for the next major iteration
- **Long Term** — Future possibility, not committed

### Rule 10: Deferred Decisions

If a decision is intentionally deferred, record it in `docs/01-Product/18-Deferred-Decisions.md` with:
- What was proposed
- Why it was deferred
- What would trigger revisiting

## 3. Document States

| State | Meaning | Requirements |
|-------|---------|--------------|
| **Draft** | Initial writing, not yet reviewed | Complete content exists |
| **Stable** | Reviewed and internally consistent but may need refinement | Peer review completed |
| **Approved** | Final, authoritative, changeable only via ADR | Product Architect sign-off |

## 4. Documentation Directory

```
docs/
├── 01-Product/          # Product-level documentation (this set)
│   ├── 00-Index.md      # Master index
│   ├── 01-Product-Bible.md
│   └── ...
├── ADR/                 # Architecture Decision Records
│   ├── _index.md         # ADR index
│   ├── 0001-*.md
│   └── ...
├── 02-Architecture/     # Technical architecture (Phase 1+)
├── 03-Implementation/   # Implementation guides (Phase 2+)
├── 04-Meetings/         # Session notes
├── 05-Decisions/        # Legacy decisions (pre-constitution)
└── 06-Research/         # Domain research
```

## 5. Maintenance Rhythm

- Documentation is updated during every development session.
- Before any architecture work, check if the relevant documents are up to date.
- After any architecture decision, update or create documents.
- The Product Bible is the entry point for all new team members.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Chief Product Architect | Initial creation from Product Discovery |
