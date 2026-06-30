---
title: Story 1.1 Create and update member records
status: ready-for-dev
created: 2026-06-29
updated: 2026-06-29
---

# Story 1.1: Create and update member records

Status: ready-for-dev

## Story

As an administrator,
I want to create and update member records,
so that the church directory stays accurate and current.

## Acceptance Criteria

1. An administrator can create a new member record from a dedicated form.
2. The system stores required member fields including full name, contact information, household, status, and division assignment.
3. Existing member records can be opened, edited, and saved without creating duplicates.
4. Validation prevents empty required fields and rejects invalid contact data formats.
5. Changes are persisted and visible in the member directory immediately after save.

## Tasks / Subtasks

- [ ] Implement the member domain model and persistence layer (AC: #1, #2, #5)
  - [ ] Define member fields and validation rules
  - [ ] Add create and update repository or service methods
- [ ] Build the member create and edit workflow in the API and UI (AC: #1, #3, #4)
  - [ ] Create a form for creating and editing member records
  - [ ] Add backend endpoints for create and update operations
- [ ] Verify directory integration and record visibility (AC: #3, #5)
  - [ ] Ensure saved records appear in directory and profile views
  - [ ] Add regression tests for create and update flows

## Dev Notes

- Follow the architecture invariants in [architecture-spine.md](_bmad-output/implementation-artifacts/architecture-spine.md) for a single source of truth and workflow-first data entry.
- Treat members as a first-class domain module with shared data access for directory, reporting, and future ministry workflows.
- Start with a simple relational model for person, household, contact details, status, and divisions.
- Keep role-based access limited to administrators and staff for create and edit actions.

### Project Structure Notes

- Implement the feature in a modular structure with distinct UI, API, and persistence layers.
- If the codebase is not yet present, create a minimal baseline for the Members module that can later support attendance and giving workflows.

### References

- [Source: docs/initial-product-brief.md](docs/initial-product-brief.md)
- [Source: _bmad-output/planning-artifacts/epics-and-stories.md](_bmad-output/planning-artifacts/epics-and-stories.md)
- [Source: _bmad-output/planning-artifacts/developer-ready-stories.md](_bmad-output/planning-artifacts/developer-ready-stories.md)
- [Source: _bmad-output/implementation-artifacts/architecture-spine.md](_bmad-output/implementation-artifacts/architecture-spine.md)

## Dev Agent Record

### Agent Model Used

MAI-Code-1-Flash

### Debug Log References

### Completion Notes List

### File List
