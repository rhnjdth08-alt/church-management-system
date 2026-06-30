---
title: Story 1.2 Assign members to divisions
status: review
created: 2026-06-29
updated: 2026-06-29
baseline_commit: 10b1972a8433e03a12fd823d8bd625f971ae30a1
---

# Story 1.2: Assign members to divisions

Status: review

## Story

As a church administrator,
I want to assign members to divisions such as Sunday School, Youth, and Adult classes,
so that ministry groups are organized and participation can be tracked.

## Acceptance Criteria

1. The member profile supports selecting one or more divisions during create and edit.
2. Division categories include at least Sunday School, Youth, and Adult class.
3. Assigned divisions are visible on the member profile and in directory listings.
4. Division assignments are persisted and available for filtering or reporting.

## Tasks / Subtasks

- [x] Define the `Division` concept in the domain model and persistence layer (AC: #1, #2, #4)
  - [x] Create a stable list of division categories and identifiers
  - [x] Add support for member-to-division assignment
- [x] Extend member create/edit workflows to support division selection (AC: #1, #3)
  - [x] Add division selection UI elements to the member form
  - [x] Persist division assignments through member save operations
- [x] Expose division data in directory and profile views (AC: #3, #4)
  - [x] Display assigned divisions where members are listed
  - [x] Confirm division assignments are queryable for future filters/reports
- [x] Add tests for division assignment, display, and persistence

## Dev Notes

- Model divisions as a lookup entity or enum to keep group categories consistent.
- Support one-to-many or many-to-many assignment based on the project data model; start with one member assigned to one primary division if simpler, then open to extension.
- Use the member module created in Story 1.1 as the integration point for division data.
- Keep the feature focused on core assignment and visibility so later filtering and reporting can reuse the same data.

## References

- [Source: _bmad-output/planning-artifacts/epics-and-stories.md](_bmad-output/planning-artifacts/epics-and-stories.md)
- [Source: _bmad-output/planning-artifacts/developer-ready-stories.md](_bmad-output/planning-artifacts/developer-ready-stories.md)
- [Source: _bmad-output/implementation-artifacts/1-1-create-and-update-member-records.md](_bmad-output/implementation-artifacts/1-1-create-and-update-member-records.md)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m]

### Debug Log References

- `pytest -q` (backend): 24 passed (15 pre-existing + 9 new).
- Red-green-refactor confirmed for all new behavior: the 8 division-assignment tests and the multi-division frontend test all failed before implementation and passed after.
- End-to-end smoke test through the real FastAPI `lifespan` verified default-division seeding, multi-division persistence, and division filtering.

### Implementation Plan

- Model "one or more divisions" (AC #1) as a many-to-many `MemberDivisionLink` association table plus a `Member.divisions` relationship, while keeping the existing single `division_id` as the member's **primary division** for backward compatibility with Story 1.1's required-field behavior and existing UI/tests.
- Expose a `division_ids` list on the member API (request: `MemberCreate`/`MemberUpdate`; response: new `MemberRead`). The primary `division_id` is always included in the assignment set on create.
- Seed the required division categories (Sunday School, Youth, Adult Class) idempotently at startup (AC #2).
- Add an optional `division_id` query filter to `GET /members` so assignments are queryable for filtering/reporting (AC #4).

### Completion Notes List

- **Domain model & persistence (AC #1, #2, #4):** Added `MemberDivisionLink` association table and `Member.divisions` / `Division.assigned_members` many-to-many relationships in [models.py](backend/app/models.py). The legacy `division_id` is retained as the primary division. `MemberRead` exposes a flattened `division_ids` list.
- **Default categories (AC #2):** `seed_default_divisions()` idempotently inserts Sunday School, Youth, and Adult Class on startup.
- **Create/edit workflow (AC #1, #3):** `POST /members` and `PUT /members/{id}` accept `division_ids`. On create the primary division is always merged into the set; on update an explicit `division_ids` list fully replaces assignments and retargets the primary division if it falls outside the new set. Division ids are validated (400 "Division not found." on any unknown id). The single-page UI gained a multi-select `#division_ids` control alongside the primary-division select.
- **Directory & profile visibility (AC #3):** `MemberRead.division_ids` powers the new "Divisions" column in the directory table and a "Divisions" row in the profile panel.
- **Queryable for filtering (AC #4):** `GET /members?division_id=<id>` joins the link table to return only members assigned to that division.
- **Test infrastructure fix:** Added [conftest.py](backend/tests/conftest.py). The existing suite was failing at baseline ("no such table: household") because the modules instantiate `TestClient(app)` without a `with` block, so the `lifespan` startup that creates tables never ran. The fixture creates/drops tables per test (isolation) and seeds default divisions to mirror startup.
- **Pre-existing bug fixed:** `lifespan` was declared `def` under `@asynccontextmanager`, which made the real app fail to start (`'generator' object is not an async iterator`) — so table creation and division seeding would never have run in production. Changed to `async def`. This is outside the literal task list but was required for the feature (and the app) to start; flagged here for the reviewer.

### File List

- backend/app/models.py (modified — `MemberDivisionLink` table, `Member.divisions` / `Division.assigned_members` relationships, `division_ids` on `MemberCreate`/`MemberRead`/`MemberUpdate`)
- backend/app/schemas.py (modified — `division_ids` on `MemberCreate`/`MemberUpdate`, new `MemberRead` schema)
- backend/app/main.py (modified — default-division seeding, `_resolve_division_ids`/`_set_member_divisions`/`_to_read` helpers, multi-division create/update, `division_id` list filter, `MemberRead` response models, `async def lifespan` fix)
- backend/app/static/index.html (modified — multi-select divisions control, directory "Divisions" column, profile divisions row, submit/load/reset wiring)
- backend/tests/conftest.py (new — per-test table create/drop + default-division seeding fixture)
- backend/tests/test_divisions_assignment.py (new — 8 tests for seeding, multi-division create/edit, validation, visibility, filtering)
- backend/tests/test_frontend.py (modified — added multi-division UI control test)

## Change Log

- 2026-06-29: Implemented Story 1.2. Added many-to-many member↔division assignment (`MemberDivisionLink`) with a `division_ids` API field while retaining `division_id` as the primary division; seeded default division categories (Sunday School, Youth, Adult Class); added a division filter to `GET /members`; extended the UI with a multi-division selector and divisions display in directory/profile. Added a `conftest.py` to fix the broken test baseline and 9 new tests. Fixed a pre-existing `lifespan` bug (`def` → `async def`) that prevented app startup. Full backend suite passes (24 tests). Status → review.
