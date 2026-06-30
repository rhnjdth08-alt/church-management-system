---
title: Story 2.1 Record attendance for services
status: review
created: 2026-06-30
updated: 2026-06-30
baseline_commit: 10b1972a8433e03a12fd823d8bd625f971ae30a1
---

# Story 2.1: Record attendance for services

Status: review

## Story

As a ministry leader,
I want to record attendance for a service or event and mark which members were present,
so that participation can be tracked over time and reviewed per person or group.

## Acceptance Criteria

1. A user can create a service/event to record attendance against, with at least a name/label and a date.
2. A user can record attendance by marking one or more members as present for a given service.
3. Each attendance entry is associated with both a date (the service date) and a specific person (member).
4. Attendance history can be viewed for a single person (the services they attended).
5. Attendance history can be viewed for a group/service (the members present at a given service).
6. Attendance is recorded against the shared member data model (no separate person list) and recording attendance does not modify member records.

## Tasks / Subtasks

- [x] Define the Attendance domain model and persistence (AC: #1, #2, #3, #6)
  - [x] Add a `Service` table (id, name, date) representing a service/event attendance is recorded against
  - [x] Add an `AttendanceRecord` table linking a `member_id` and `service_id` (unique per member+service to prevent duplicates), carrying the service date for convenient per-person history
  - [x] Add relationships so a service exposes its attendees and a member exposes their attendance; ensure both new tables are registered for `create_db_and_tables`
- [x] Add Attendance API endpoints (AC: #1, #2, #3, #4, #5)
  - [x] `POST /services` and `GET /services` (create + list services), mirroring the `divisions`/`tags` endpoint style
  - [x] `POST /services/{service_id}/attendance` to record attendance — accept a list of member ids to mark present; validate the service and each member exists (400 on unknown); be idempotent (re-recording the same member for the same service must not create duplicates)
  - [x] `GET /services/{service_id}/attendance` returns the members present at that service (group/service history, AC #5)
  - [x] `GET /members/{member_id}/attendance` returns the services that member attended (per-person history, AC #4)
- [x] Surface attendance in the UI (AC: #1, #2, #4, #5)
  - [x] Add a minimal Attendance section/panel: create a service (name + date), then check off present members from the existing directory/member list and save
  - [x] Show a member's attendance history in the member profile panel
  - [x] Keep it consistent with the existing single-page UI style (cards, fetch helpers); optimize for fast entry per AD-4
- [x] Add tests for attendance recording and history (AC: #1–#6)
  - [x] API tests: create/list services; record attendance for one or more members; idempotent re-record (no duplicates); invalid service/member rejected; per-person history; per-service history
  - [x] Confirm recording attendance does not mutate member records (member count/fields unchanged)
  - [x] Frontend test: assert the attendance UI controls are present in the served page

## Dev Notes

### This is a new domain module — but reuse the established backend patterns exactly

Epic 1 (Stories 1.1–1.3) established firm conventions. Follow them so this module is consistent and the tests run:

- **Models** live in [backend/app/models.py](backend/app/models.py) as SQLModel `table=True` classes. Look at `Division` + `MemberDivisionLink` and `Tag` + `MemberTagLink` for the table + relationship pattern. For attendance use a `Service` entity and an `AttendanceRecord` association (member ↔ service). Prefer a composite/unique constraint on `(member_id, service_id)` so re-recording is naturally de-duplicated.
- **Schemas** (request/response shapes) live in [backend/app/schemas.py](backend/app/schemas.py) as SQLModel classes (e.g. `ServiceCreate`, an attendance request body, and read models). The API returns explicit read schemas, not raw table models, for member-facing data — see `MemberRead` and the `_to_read` serializer.
- **Endpoints** live in [backend/app/main.py](backend/app/main.py). Mirror `POST/GET /divisions` and `POST/GET /tags` for `POST/GET /services`. Use `session: Session = Depends(get_session)`. Validate foreign keys with `session.get(Model, id)` and raise `HTTPException(status_code=400, detail="… not found.")` exactly like the existing member/division/tag validation.
- **DB registration:** new tables must exist before tests run. `create_db_and_tables()` calls `SQLModel.metadata.create_all`. Tables are registered by importing the models — [backend/app/database.py](backend/app/database.py) imports `Member` to register metadata; ensure the new `Service`/`AttendanceRecord` classes are imported on the path that runs before table creation (they will be, since `main.py` imports from `.models`). The test fixture (below) drops/creates all tables, so new tables are picked up automatically.

### Integration point: the Member model (do NOT create a parallel person list)

- Attendance references existing members by `member_id` (FK to `member.id`). The `Member` model already exists with `id`, `first_name`, `last_name`, `status`, `household_id`, `division_id`, plus `divisions` and `tags` relationships. [Source: backend/app/models.py]
- Per **AD-1 (single source of truth)**, attendance must point at the shared `Member` records, not copy names. The member directory (`GET /members`, already supports search/filter from Story 1.3) is the natural place to pick people to mark present.

### Files to touch

- **UPDATE** [backend/app/models.py](backend/app/models.py) — add `Service` and `AttendanceRecord` tables + relationships.
- **UPDATE** [backend/app/schemas.py](backend/app/schemas.py) — add `ServiceCreate` (name, date), an attendance request schema (e.g. `member_ids: list[int]`), and read schemas for service and attendance history.
- **UPDATE** [backend/app/main.py](backend/app/main.py) — add the services + attendance endpoints; add small serializer helpers in the style of `_to_read`.
- **UPDATE** [backend/app/static/index.html](backend/app/static/index.html) — add the attendance entry UI and per-member history display. Reuse the `api()` fetch helper, `$()` shortcut, card layout, and the existing `members`/directory rendering.
- **NEW** `backend/tests/test_attendance.py` — attendance API + history tests.
- **UPDATE** [backend/tests/test_frontend.py](backend/tests/test_frontend.py) — assert the attendance UI controls render.

### Dates — keep it simple and JSON-friendly

- Store the service date as a date/datetime via SQLModel (`datetime.date` is fine with SQLite). Accept it as an ISO string (`"2026-06-30"`) in the request and return it as a string in responses — matches how the vanilla-JS UI sends/receives JSON. Do not add a date-picker library; a native `<input type="date">` is sufficient.
- **Avoid `Date.now()`/`datetime.now()` non-determinism in tests** — pass explicit dates in test payloads so assertions are stable.

### Testing standards (match existing patterns — non-negotiable for green tests)

- Framework: **pytest** + FastAPI `TestClient`. Tests live in `backend/tests/`, instantiate `client = TestClient(app)` at module top.
- **Critical:** tests rely on [backend/tests/conftest.py](backend/tests/conftest.py) — an autouse `fresh_database` fixture that drops/creates ALL tables per test and seeds default divisions. The app `lifespan` does NOT run under a bare `TestClient`, so do not assume startup side effects beyond what conftest provides. Your new tables are created automatically by `SQLModel.metadata.create_all` in the fixture (no fixture change needed unless you add startup seed data).
- `lifespan` in main.py must remain `async def`.
- Run from the `backend` directory: `python -m pytest -q`. Current baseline is **42 passing**; keep all green and add attendance tests.
- `backend/church.db` is gitignored and regenerated by tests — don't commit it.
- Follow red-green-refactor: write failing tests first, then implement minimally, then refactor.

### Architecture compliance

- **AD-1 (single source of truth):** attendance references shared `Member` records. [Source: _bmad-output/implementation-artifacts/architecture-spine.md#AD-1]
- **AD-3 (domain-oriented modules):** this is the **Attendance Module** — keep it cohesive within `backend/app`. [Source: architecture-spine.md#4-suggested-module-boundaries]
- **AD-4 (workflow-first data entry):** recording attendance should be fast — mark multiple members present in one action rather than one request per person. [Source: architecture-spine.md#AD-4]
- **AD-5 (reporting from the same data model):** attendance history (per person, per service) is read straight from `AttendanceRecord`, enabling later trend reporting (Story 2.2) without a separate store. [Source: architecture-spine.md#AD-5]
- **AD-2 (RBAC):** deferred — no auth layer exists in the baseline and no AC here requires it, consistent with Stories 1.1–1.3.

### Project Structure Notes

- Modular FastAPI backend: `backend/app/` (`main.py`, `models.py`, `schemas.py`, `database.py`, `static/index.html`) + `backend/tests/`. This story stays within those files plus one new test module. Stack (FastAPI + SQLModel + SQLite + vanilla-JS SPA) is already in place — **no new dependencies required**.
- This is the first story of Epic 2 (Attendance). It establishes the attendance data model that Story 2.2 (track attendance by division) will build on, so model `AttendanceRecord` so it can later be grouped by division (the member already carries division data).

### References

- [Source: _bmad-output/planning-artifacts/epics-and-stories.md#story-21-record-attendance-for-services]
- [Source: _bmad-output/planning-artifacts/prd.md#72-attendance] (FR: record attendance for services/events; view history by person, family, or event)
- [Source: _bmad-output/implementation-artifacts/architecture-spine.md] (AD-1, AD-3, AD-4, AD-5; Attendance Module; Attendance Record data concept)
- [Source: _bmad-output/implementation-artifacts/1-3-search-and-filter-the-directory.md] (Tag/Division many-to-many + endpoint patterns, conftest test setup, serializer style)
- [Source: backend/app/models.py] (Member integration point; Division/Tag link-table patterns to mirror)
- [Source: backend/app/main.py] (endpoint + FK-validation patterns to mirror)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m]

### Debug Log References

- `pytest -q` (backend): 52 passed (42 pre-existing + 10 new).
- Red-green-refactor confirmed: the 9 new attendance backend tests and 1 new frontend test all failed before implementation and passed after.
- End-to-end smoke test through the real FastAPI `lifespan`: created services, recorded multi-member attendance, verified idempotent re-record (count stays 2), per-service attendance, and per-person history with dates.

### Implementation Plan

- New **Attendance module** within the existing backend, following Epic 1 conventions (SQLModel tables, FastAPI endpoints with `session.get` FK validation, conftest test setup, async lifespan).
- `Service` (id, name, date) is the thing attendance is recorded against. `AttendanceRecord` (id, member_id, service_id, date) is the member↔service association, with a `UniqueConstraint(member_id, service_id)` so recording is naturally idempotent. The service date is denormalized onto the record for convenient per-person history.
- Endpoints: `POST/GET /services`; `POST /services/{id}/attendance` (mark a list of members present, validating service + each member); `GET /services/{id}/attendance` (present members, AC #5); `GET /members/{id}/attendance` (per-person history, AC #4).
- UI: an Attendance card to create a service (name + native date input) and check off present members in one save (AD-4 fast entry); the profile panel shows the member's attendance history.

### Completion Notes List

- **Domain model (AC #1, #3, #6):** Added `Service` and `AttendanceRecord` tables in [models.py](backend/app/models.py). `AttendanceRecord` has a `UniqueConstraint(member_id, service_id)` enforcing one row per member per service. The service `date` (a `datetime.date`) is stored on each record so per-person history needs no extra join for the date. Tables register automatically via `main.py`'s import of `.models`, so `create_db_and_tables` and the test fixture pick them up.
- **Endpoints (AC #1–#5):** Added in [main.py](backend/app/main.py). `record_attendance` validates the service (404 "Service not found.") and every member (400 "Member not found.") up front, then inserts only members not already present — idempotent without relying on a DB error. `_present_members` serializes attendees as `MemberRead` (reusing `_to_read`). History returns `AttendanceHistoryEntry` rows (service_id, name, date).
- **Schemas:** Added `ServiceCreate`/`ServiceRead`, `AttendanceCreate` (`member_ids` list), and `AttendanceHistoryEntry` in [schemas.py](backend/app/schemas.py). Dates are exchanged as ISO strings via `datetime.date`.
- **UI (AC #1, #2, #4, #5):** Added a "Record Attendance" card to [index.html](backend/app/static/index.html) — create a service (name + `<input type="date">`), pick a service, check off present members, and Save (one request marks all present, per AD-4). The member profile now shows an Attendance row with the member's attended services + dates. Reuses the existing `api()`/`$()` helpers and card styling; no new libraries.
- **Regression safety (AC #6):** All 42 prior tests still pass. A dedicated test confirms recording attendance does not change member count or fields. RBAC (AD-2) remains deferred, consistent with Epic 1.
- **Forward compatibility:** `AttendanceRecord` references the member (which already carries division data), so Story 2.2 (attendance by division) can group on it without schema changes.

### File List

- backend/app/models.py (modified — `date`/`UniqueConstraint` imports; `Service`/`ServiceCreate`, `AttendanceRecord` tables + relationships)
- backend/app/schemas.py (modified — `date` import; `ServiceCreate`, `ServiceRead`, `AttendanceCreate`, `AttendanceHistoryEntry`)
- backend/app/main.py (modified — attendance model/schema imports; `POST/GET /services`, `POST/GET /services/{id}/attendance`, `GET /members/{id}/attendance`, `_present_members` helper)
- backend/app/static/index.html (modified — Record Attendance card, service create + member checklist + save wiring, profile attendance history, `.checklist` styles, initial `loadAttendance`)
- backend/tests/test_attendance.py (new — 9 tests: service create/list, record one/many, idempotent re-record, invalid service/member, per-person history, per-service history, no member mutation)
- backend/tests/test_frontend.py (modified — added attendance UI controls test)

## Change Log

- 2026-06-30: Implemented Story 2.1. Introduced the Attendance module — `Service` + `AttendanceRecord` (unique per member+service for idempotent recording, service date denormalized for history). Added `POST/GET /services`, `POST/GET /services/{id}/attendance`, and `GET /members/{id}/attendance`. Extended the UI with a Record Attendance card (create service, mark members present in one save) and attendance history in the member profile. Added 10 tests (now 52 passing). Opened Epic 2. Status → review.
