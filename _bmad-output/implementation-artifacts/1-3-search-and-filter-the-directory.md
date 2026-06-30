---
title: Story 1.3 Search and filter the directory
status: review
created: 2026-06-29
updated: 2026-06-30
baseline_commit: 10b1972a8433e03a12fd823d8bd625f971ae30a1
---

# Story 1.3: Search and filter the directory

Status: review

## Story

As a staff member,
I want to search and filter the member directory by name, household, status, division, and ministry tag,
so that I can find people quickly without scrolling the whole list.

## Acceptance Criteria

1. A user can search members by name (first or last, case-insensitive, partial match) and see the directory narrow to matching members.
2. A user can search/filter members by household.
3. A user can filter members by status (active/inactive).
4. A user can filter members by division.
5. A user can filter members by ministry tag.
6. Search and filters combine (an active search term AND active filters all apply together with AND semantics), and clearing them restores the full directory.
7. Filtering/searching returns results from the shared member data layer (no separate data source) and does not alter or duplicate records.

> **Ministry tags — new in this story.** The baseline data model had no tag concept. This story introduces ministry tags as **reusable first-class entities** modeled exactly like divisions: a `Tag` table plus a `MemberTagLink` many-to-many association, with `GET/POST /tags` endpoints and a `tag_ids` list on the member API. This keeps tags standardized (admins pick from a shared list, no free-text typos) and queryable for filtering/reporting — consistent with AD-1 and the existing division pattern.

## Tasks / Subtasks

- [x] Introduce the ministry `Tag` concept in the domain model and API (AC: #5)
  - [x] Add a `Tag` table (id, name, optional description) and a `MemberTagLink` many-to-many association, modeled like `Division`/`MemberDivisionLink`
  - [x] Add `Member.tags` relationship and expose a flattened `tag_ids` list on `MemberRead`
  - [x] Add `GET /tags` and `POST /tags` endpoints (mirroring `GET/POST /divisions`)
  - [x] Accept `tag_ids` on `MemberCreate`/`MemberUpdate`; validate ids (400 "Tag not found." on unknown id) and persist links on create/update (replace-on-update like divisions, but tags are optional — empty/omitted means no tags)
- [x] Extend `GET /members` to accept search and filter query parameters (AC: #1, #2, #3, #4, #5, #6, #7)
  - [x] Add `q` (name search), `household_id`, `status`, `tag_id`, and reuse existing `division_id` query params; all optional and combinable (AND semantics)
  - [x] Make name search case-insensitive partial match across first_name and last_name
  - [x] Keep the existing `division_id` filter behavior intact (it already joins `MemberDivisionLink`); filter by `tag_id` via a `MemberTagLink` join the same way
  - [x] Return results via the existing `MemberRead` response (no new data source; no record mutation)
- [x] Add search and filter controls to the directory UI (AC: #1, #2, #3, #4, #5, #6)
  - [x] Add a name search input, plus household / status / division / tag filter selects above the directory table
  - [x] Add a "Tags" multi-select to the member create/edit form and a quick-add (mirroring the division multi-select + inline add from Story 1.2)
  - [x] Show assigned tags in the directory row and profile panel
  - [x] Re-query `GET /members` with the active params on input/change (debounced for the text input)
  - [x] Add a "Clear" control that resets all search/filter inputs and reloads the full directory
- [x] Add tests for tags, search, and filter behavior (AC: #1–#7)
  - [x] Tag API tests: create/list tags, assign one or more tags to a member on create and update, invalid tag id rejected
  - [x] Filter tests: name search (partial, case-insensitive), household filter, status filter, division filter, tag filter, combined search+filters, and empty/no-match results
  - [x] Confirm filtering does not create or modify records (count/identity unchanged)
  - [x] Frontend test: assert the search input, filter selects, and tag controls are present in the served UI

## Dev Notes

### What already exists (reuse — do NOT reinvent)

- **The division filter is already implemented.** `GET /members?division_id=<id>` joins `MemberDivisionLink` and returns only members in that division. Extend this same endpoint; do not create a new one. [Source: backend/app/main.py — `list_members`]
- **Member data model:** `Member` has `first_name`, `last_name`, `email`, `phone`, `status` (default `"active"`), `household_id` (FK), `division_id` (primary division), and a many-to-many `divisions` set via `MemberDivisionLink`. The API response model `MemberRead` exposes a flattened `division_ids` list. [Source: backend/app/models.py, backend/app/schemas.py]
- **Lookups for filter dropdowns already exist:** `GET /households` and `GET /divisions` return the lists the UI needs to populate household/division filter selects. The frontend already loads these into `households` / `divisions` arrays in [index.html](backend/app/static/index.html) via `loadLookups()`.
- **Status values** in use are `"active"` and `"inactive"` (see the status `<select>` in the form).

### Ministry tags — model exactly like divisions (reuse the proven pattern)

Story 1.2 established the many-to-many pattern for divisions. Replicate it for tags so the dev agent doesn't invent a new shape:
- `Tag(SQLModel, table=True)` with `id`, `name`, optional `description` — parallels `Division`.
- `MemberTagLink(SQLModel, table=True)` with `member_id`/`tag_id` composite PK — parallels `MemberDivisionLink`.
- `Member.tags: List[Tag]` relationship via `link_model=MemberTagLink`; `MemberRead.tag_ids: List[int]`.
- `GET/POST /tags` mirror `GET/POST /divisions`.
- Reuse the helper style from [main.py](backend/app/main.py): validate ids and call a `_set_member_tags` analogous to `_set_member_divisions`; include `tag_ids` in `_to_read`.
- **Difference from divisions:** tags are fully optional. There is no "primary tag" and no required-field check — a member may have zero tags. Default to an empty list. Do NOT seed any default tags (unlike divisions, there are no mandated tag categories).

### Files to touch

- **UPDATE** [backend/app/main.py](backend/app/main.py) — extend the `list_members` endpoint with optional `q`, `household_id`, `status` query params alongside the existing `division_id`. Build the SQLModel `select(Member)` statement conditionally; for `q`, use a case-insensitive `LIKE`/`ilike`-style match on `first_name` and `last_name` (SQLite `LIKE` is case-insensitive for ASCII by default). When `division_id` is present, preserve the existing `MemberDivisionLink` join. Return `[_to_read(m) for m in members]`.
- **UPDATE** [backend/app/static/index.html](backend/app/static/index.html) — current `loadDirectory()` calls `api("/members")` with no params. Change it to assemble a query string from the active search/filter controls (a `URLSearchParams` of `q`, `household_id`, `status`, `division_id`, omitting empty values). Add the controls in the "Directory" card above the table, wire `input`/`change` listeners (debounce the text input ~250ms) to call `loadDirectory()`, and add a Clear button that resets inputs and reloads. Reuse the existing `households`/`divisions` arrays and `fillSelect` helper to populate the household/division filter selects (add a leading "All" option).
- **UPDATE** [backend/tests/test_frontend.py](backend/tests/test_frontend.py) or a new test file — assert the search/filter controls render.

### Current behavior that must be preserved (regression guardrails)

- `GET /members` with **no params** must still return all members (the existing directory load and several existing tests depend on this). All new params are optional.
- The existing `division_id` filter semantics (join via `MemberDivisionLink`, exact membership) must not change — `test_filter_members_by_division` in [test_divisions_assignment.py](backend/tests/test_divisions_assignment.py) must keep passing.
- The UI's directory still renders the Name/Email/Phone/Status/Household/Divisions columns and row-click-to-profile behavior — search/filter only changes which rows are fetched, not how a row renders.

### Testing standards (match existing patterns)

- Framework: **pytest** with FastAPI `TestClient`. Tests live in `backend/tests/` and instantiate `client = TestClient(app)` at module top.
- **Critical:** tests rely on [backend/tests/conftest.py](backend/tests/conftest.py) — an autouse `fresh_database` fixture that drops/creates all tables per test and seeds the default divisions (Sunday School, Youth, Adult Class). The app's `lifespan` does NOT run under a bare `TestClient`, so do not assume startup-seeded data beyond what conftest provides. New tables/seed data needed at startup must also be mirrored in the fixture.
- `lifespan` in main.py must remain `async def` (a prior `def` caused `'generator' object is not an async iterator` and prevented startup).
- Run the suite from the `backend` directory: `python -m pytest -q`. The current baseline is **24 passing**; this story should add tests and keep all green.
- `backend/church.db` is gitignored and regenerated by tests — don't commit it.

### Architecture compliance

- **AD-1 (single source of truth)** and **AD-5 (reporting from the same data model):** search/filter must query the shared member data layer (the `Member` table), not a copy or cache. [Source: _bmad-output/implementation-artifacts/architecture-spine.md#2-core-architectural-invariants]
- **AD-3 (domain-oriented modules):** keep this within the Members module (`backend/app`). [Source: architecture-spine.md#4-suggested-module-boundaries]
- **AD-2 (role-based access control):** the architecture calls for RBAC, but no authentication layer exists in the baseline and no AC in this story requires it. As in Story 1.1, RBAC is deferred to a dedicated security story — do not add auth here. [Source: architecture-spine.md#AD-2]

### Project Structure Notes

- Modular FastAPI backend: `backend/app/` (app code: `main.py`, `models.py`, `schemas.py`, `database.py`, `static/index.html`) and `backend/tests/` (pytest). This story stays entirely within those files — no new modules or libraries are required. The stack (FastAPI + SQLModel + SQLite + vanilla-JS single-page UI) is already in place from Stories 1.1 and 1.2.
- No new dependencies needed; search/filter is standard query-parameter work on the existing endpoint.

### References

- [Source: _bmad-output/planning-artifacts/epics-and-stories.md#story-13-search-and-filter-the-directory]
- [Source: _bmad-output/planning-artifacts/prd.md#71-member-management] (FR: "Search and filter the directory by name, household, status, or tag")
- [Source: _bmad-output/implementation-artifacts/architecture-spine.md]
- [Source: _bmad-output/implementation-artifacts/1-2-assign-members-to-divisions.md] (division filter, data model, test setup precedents)
- [Source: backend/app/main.py] (existing `list_members` with `division_id` filter)
- [Source: backend/app/models.py] (Member / Division / MemberDivisionLink)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m]

### Debug Log References

- `pytest -q` (backend): 42 passed (24 pre-existing + 18 new).
- Red-green-refactor confirmed: the 16 new backend tests (tags + search/filter) and 2 new frontend tests all failed before implementation and passed after.
- End-to-end smoke test through the real FastAPI `lifespan` verified tag create/assign/clear, name search, status/tag filters, and combined AND-semantics filtering.
- Resolved a SQLAlchemy autoflush warning ("object not in session") by adding the new member to the session before assigning division/tag relationships in `create_member`.

### Completion Notes List

- **Ministry tags as first-class entities (AC #5):** Added `Tag` table + `MemberTagLink` many-to-many association in [models.py](backend/app/models.py), modeled on the Story 1.2 division pattern. `Member.tags` relationship; `MemberRead.tag_ids` flattened list. `GET/POST /tags` mirror the division endpoints. Tags are fully optional — no primary tag, no required-field check, no seeded defaults.
- **Tag assignment on create/edit:** `POST /members` and `PUT /members/{id}` accept `tag_ids`; ids are validated (400 "Tag not found.") and persisted via `_resolve_tag_ids`/`_set_member_tags`. On update an explicit `tag_ids` list fully replaces tags, and an explicit empty list clears them (tracked via `tag_ids_provided` so omitting the field leaves tags untouched).
- **Search & filter (AC #1–#7):** `GET /members` gained optional `q`, `household_id`, `status`, `tag_id` params alongside the existing `division_id`, combined with AND semantics by building the `select(Member)` statement incrementally. Name search is a case-insensitive partial match on first/last name via `func.lower(...).like(...)`. The `division_id` filter behavior is unchanged; `tag_id` filters via a `MemberTagLink` join the same way. No params still returns all members.
- **UI (AC #1–#6):** [index.html](backend/app/static/index.html) gained a filter bar (name search input + household/status/division/tag selects + Clear button) above the directory, a "Tags" multi-select with quick-add in the member form, and Tags shown in the directory column and profile panel. The directory re-queries with the active filter params (search input debounced ~250ms); Clear resets everything and reloads.
- **Regression safety:** All 24 prior tests still pass. The no-param `/members` behavior, the division filter semantics, and existing UI behaviors are preserved. RBAC (architecture AD-2) remains deferred, consistent with Stories 1.1–1.2 — no AC here requires auth.

### File List

- backend/app/models.py (modified — `MemberTagLink` table, `Tag`/`TagCreate`, `Member.tags` relationship, `tag_ids` on `MemberCreate`/`MemberRead`/`MemberUpdate`)
- backend/app/schemas.py (modified — `TagCreate`, `tag_ids` on `MemberCreate`/`MemberUpdate`/`MemberRead`)
- backend/app/main.py (modified — `GET/POST /tags`, `_resolve_tag_ids`/`_set_member_tags`, tags in `_to_read` and create/update, search/filter query params on `list_members`, `func` import, session-add-before-relationship fix)
- backend/app/static/index.html (modified — directory filter bar, tag multi-select + quick-add, Tags column/profile row, filter query + debounce + Clear wiring)
- backend/tests/test_tags.py (new — 7 tests: tag create/list, assign on create/update, optional/empty, invalid-id, clear)
- backend/tests/test_search_filter.py (new — 9 tests: name search, household/status/division/tag filters, combined, no-params, no-mutation)
- backend/tests/test_frontend.py (modified — added search/filter controls test and tag control test)

## Change Log

- 2026-06-30: Implemented Story 1.3. Introduced ministry tags as reusable first-class entities (`Tag` + `MemberTagLink`) with `GET/POST /tags` and `tag_ids` on the member API. Added directory search and filtering on `GET /members` (`q`, `household_id`, `status`, `division_id`, `tag_id`, combinable with AND semantics; case-insensitive name search). Extended the UI with a filter bar, tag multi-select + quick-add, and Tags display in directory/profile. Added 18 tests (now 42 passing) and fixed a SQLAlchemy autoflush warning. Status → review.
