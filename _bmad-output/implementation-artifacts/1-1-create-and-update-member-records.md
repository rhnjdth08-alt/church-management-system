---
title: Story 1.1 Create and update member records
status: review
created: 2026-06-29
updated: 2026-06-29
baseline_commit: 10b1972a8433e03a12fd823d8bd625f971ae30a1
---

# Story 1.1: Create and update member records

Status: review

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

- [x] Implement the member domain model and persistence layer (AC: #1, #2, #5)
  - [x] Define member fields and validation rules
  - [x] Add create and update repository or service methods
- [x] Build the member create and edit workflow in the API and UI (AC: #1, #3, #4)
  - [x] Create a form for creating and editing member records
  - [x] Add backend endpoints for create and update operations
- [x] Verify directory integration and record visibility (AC: #3, #5)
  - [x] Ensure saved records appear in directory and profile views
  - [x] Add regression tests for create and update flows

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

- `pytest -q` (backend): 15 passed.
- Red-green-refactor cycles confirmed for phone validation, list endpoints, and frontend serving (tests failed before implementation, passed after).

### Completion Notes List

- **Domain model & persistence** were already present (SQLModel `Member`/`Household`/`Division`, SQLite via `database.py`). Strengthened validation rules by adding phone-format validation (`_is_valid_phone`) on both create and update, complementing the existing required-name and email-format checks (AC #2, #4).
- **Create/edit workflow**: backend `POST /members` and `PUT /members/{id}` were in place. Added `GET /households` and `GET /divisions` so the UI can populate household/division selectors, and built a dedicated single-page UI (`backend/app/static/index.html`) served at `/` with a create/edit form, inline quick-add for households/divisions, and client-side validation messaging (AC #1, #3, #4).
- **Directory & profile integration**: `GET /members` powers the directory; clicking a row opens a profile panel; saving reloads the directory immediately so new/updated records are visible at once (AC #3, #5). Editing reuses the same record via `PUT` — no duplicates.
- Added regression tests covering phone validation, list endpoints, frontend serving, directory visibility, profile updates, and the no-duplicate-on-edit guarantee.
- **Deferred / out of scope**: Dev Notes mention role-based access for admins/staff (architecture AD-2). No authentication layer exists in the baseline and no acceptance criterion in this story covers auth, so RBAC is intentionally left for a dedicated security story rather than implemented here.

### File List

- backend/app/main.py (modified — phone validation, `GET /households`, `GET /divisions`, root UI route, static mount)
- backend/app/static/index.html (new — member directory + create/edit form + profile UI)
- backend/tests/test_members.py (modified — added phone validation tests)
- backend/tests/test_api_listing.py (new — household/division list endpoint tests)
- backend/tests/test_frontend.py (new — root UI serving test)
- backend/tests/test_directory_integration.py (new — directory visibility, profile, no-duplicate tests)

## Change Log

- 2026-06-29: Implemented Story 1.1. Added phone-format validation, `GET /households` and `GET /divisions` endpoints, and a dedicated single-page member UI (create/edit form, directory, profile) served at `/`. Added regression tests; full backend suite passes (15 tests). Status → review.
