---
title: Story 2.2 Track attendance by division
status: ready-for-dev
created: 2026-06-30
updated: 2026-06-30
baseline_commit: 10b1972a8433e03a12fd823d8bd625f971ae30a1
---

# Story 2.2: Track attendance by division

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a class leader,
I want to track attendance by division (e.g. Sunday School, Youth, Adult Class),
so that participation in each ministry group is visible by date and class, and I can compare engagement across divisions.

## Acceptance Criteria

1. Attendance recorded for a service can be attributed to a division: for any given service, a leader can see how many (and which) of the present members belong to a given division.
2. A per-division attendance summary is viewable by date and class — for a division, return the services (with dates) and the count of present members of that division at each.
3. Leaders can compare participation across divisions — a summary endpoint returns, for a given service (or overall), present-member counts grouped by division so divisions can be compared side by side.
4. Division attendance is derived from the **existing** shared data model (`AttendanceRecord` + member↔division links). No new attendance store, and no duplication of member/division data (AD-1, AD-5).
5. Recording attendance is unchanged and non-destructive: existing Story 2.1 endpoints and the member records are not modified by this story. All 52 existing tests still pass.
6. The UI surfaces division attendance: when viewing a service's attendance, a per-division breakdown (division name + present count) is shown, consistent with the existing single-page UI style.

## Tasks / Subtasks

- [x] Add division-attendance read schemas (AC: #1, #2, #3)
  - [x] In [backend/app/schemas.py](backend/app/schemas.py), add `DivisionAttendanceCount` (`division_id: int`, `division_name: str`, `present: int`) for per-division counts at a service.
  - [x] Add `DivisionAttendanceSummaryEntry` (`service_id: int`, `name: str`, `date: date`, `present: int`) for a division's per-service history (mirrors `AttendanceHistoryEntry` plus a count).
  - [x] Reuse `date` import already present; follow the existing SQLModel-class style (no raw table models in responses).
- [x] Add division-attendance endpoints (AC: #1, #2, #3, #4)
  - [x] `GET /services/{service_id}/attendance/by-division` → list of `DivisionAttendanceCount`: for the service, count present members per division. Validate the service exists (404 "Service not found." — match `list_service_attendance`). Derive counts from `AttendanceRecord` joined to `MemberDivisionLink` (a member counts toward every division they belong to). Include only divisions that have ≥1 present member (do NOT invent zero rows for unrelated divisions).
  - [x] `GET /divisions/{division_id}/attendance` → list of `DivisionAttendanceSummaryEntry`: for the division, the services its members attended with the present-count per service. Validate the division exists (400 "Division not found." — match the existing division-validation message/style). Order by service date is not required by tests but keep output deterministic.
  - [x] Add a small serializer/aggregation helper near `_present_members` (e.g. `_division_counts(session, service_id)`); reuse `session.get`/`select` patterns. Do NOT add new model tables.
- [x] Surface division attendance in the UI (AC: #6)
  - [x] In [backend/app/static/index.html](backend/app/static/index.html), within the existing `#attendance-panel`, add a per-division breakdown region with a stable id (e.g. `id="attendance-by-division"`) that renders division name + present count after attendance is loaded/saved for the selected service.
  - [x] Wire it through the existing `api()` helper: after `saveAttendance()` and when the selected service changes, fetch `/services/{id}/attendance/by-division` and render the breakdown. Reuse `$()`, the card/checklist styling, and existing rendering idioms — no new libraries, no date-picker.
  - [x] Keep it additive: the existing service-create / member-checklist / save flow must keep working unchanged.
- [x] Add tests (AC: #1–#6)
  - [x] NEW `backend/tests/test_division_attendance.py` (pytest + `TestClient(app)` at module top, per the existing pattern). Cover: per-service by-division counts (members in different divisions counted correctly; a member in two divisions counts in both); per-division per-service summary with present counts; invalid service → 404; invalid division → 400; a division with no attendance returns `[]`; cross-division comparison (two divisions, different counts).
  - [x] Assert AC #5 regression safety: recording/reading division attendance does not change member count or fields, and existing 2.1 endpoints still behave.
  - [x] UPDATE [backend/tests/test_frontend.py](backend/tests/test_frontend.py): assert the new division-breakdown control (`id="attendance-by-division"`) is present in the served page.
  - [x] Pass explicit dates in payloads (no `datetime.now()`); keep assertions deterministic.

## Dev Notes

### Build on Story 2.1 — do NOT re-architect attendance

Story 2.1 (`review`) already built the Attendance module and **explicitly designed it so this story needs no schema change**:

> "`AttendanceRecord` references the member (which already carries division data), so Story 2.2 (attendance by division) can group on it without schema changes." [Source: _bmad-output/implementation-artifacts/2-1-record-attendance-for-services.md#Completion Notes List]

This story is **read-side aggregation only**. The data already exists:
- `AttendanceRecord(id, member_id, service_id, date)` with `UniqueConstraint(member_id, service_id)`. [Source: backend/app/models.py:153-169]
- `Service(id, name, date)` with `attendance` relationship. [Source: backend/app/models.py:144-146]
- `Member` ↔ `Division` many-to-many via `MemberDivisionLink(member_id, division_id)`, plus a legacy primary `Member.division_id`. [Source: backend/app/models.py:8-16, 90-101]

**Anti-pattern to avoid:** Do NOT add a `division_id` column to `AttendanceRecord`, and do NOT create a separate division-attendance table. A present member's divisions come from their existing `MemberDivisionLink` rows. Adding a column would duplicate member data and violate AD-1 (single source of truth). The `developer-ready-stories.md` note "Add division field to attendance records" is **superseded** by 2.1's denormalized-member-link design — follow the code, not that planning note.

**Division membership semantics:** A member can belong to one or more divisions (`Member.divisions` / `MemberDivisionLink`). Count a present member toward **every** division they belong to. Use the many-to-many link (`MemberDivisionLink`), not the legacy scalar `Member.division_id`, so members assigned to multiple divisions are represented correctly and consistently with Story 1.2/1.3.

### Reuse the established backend patterns exactly

- **Schemas** live in [backend/app/schemas.py](backend/app/schemas.py) as `SQLModel` classes. `date` is already imported. Mirror `AttendanceHistoryEntry` (service_id/name/date) for the per-division summary shape. [Source: backend/app/schemas.py:1-4, 84-89]
- **Endpoints** live in [backend/app/main.py](backend/app/main.py). Mirror the existing attendance endpoints:
  - Service-not-found is **404** ("Service not found.") — see `list_service_attendance`/`record_attendance`. [Source: backend/app/main.py:338-340, 366-367]
  - Division/Member validation in this codebase uses **400** with "Division not found." / "Member not found." — see `_resolve_division_ids` and `record_attendance`. Use **400 "Division not found."** for the `/divisions/{id}/attendance` endpoint to match the existing division-validation convention. [Source: backend/app/main.py:124-125, 342-344]
  - Use `session.get(Model, id)` for existence checks and `select(...)` for aggregation, with `session: Session = Depends(get_session)`. [Source: backend/app/main.py:312-402]
  - Add a helper near `_present_members` for the per-division count aggregation; return read schemas, never raw table rows. [Source: backend/app/main.py:392-402]
- **DB registration:** No new tables, so nothing new to register. `create_db_and_tables()` / the test fixture already create all existing tables. [Source: backend/app/database.py via backend/tests/conftest.py:26-28]

### Aggregation approach (concrete)

For `GET /services/{service_id}/attendance/by-division`:
- Get present member ids: `select(AttendanceRecord.member_id).where(AttendanceRecord.service_id == service_id)`.
- For each division, count how many present members link to it. A clean single-query option:
  `select(Division.id, Division.name, func.count(...)).join(MemberDivisionLink, ...).join(AttendanceRecord, AttendanceRecord.member_id == MemberDivisionLink.member_id).where(AttendanceRecord.service_id == service_id).group_by(Division.id)`.
  Both `func` and `select` are already imported in main.py. [Source: backend/app/main.py:9] A simple in-Python aggregation over `_present_members` + each member's `divisions` is equally acceptable and easier to verify — prefer whichever is clearest; correctness over cleverness.
- Only include divisions with `present >= 1`.

For `GET /divisions/{division_id}/attendance`:
- Validate division (400 if missing). Find members of the division via `MemberDivisionLink`, then their `AttendanceRecord`s grouped by service, counting present members of that division per service. Return one `DivisionAttendanceSummaryEntry` per service the division participated in.

### Files to touch

- **UPDATE** [backend/app/schemas.py](backend/app/schemas.py) — add `DivisionAttendanceCount`, `DivisionAttendanceSummaryEntry`.
- **UPDATE** [backend/app/main.py](backend/app/main.py) — add the two GET endpoints + an aggregation helper; import the new schemas. `Division`, `MemberDivisionLink`, `AttendanceRecord`, `Service`, `func`, `select` are already imported. [Source: backend/app/main.py:9-21]
- **UPDATE** [backend/app/static/index.html](backend/app/static/index.html) — add the `#attendance-by-division` breakdown region in `#attendance-panel`; fetch+render via `api()`/`$()`. [Source: backend/app/static/index.html:116-139, 311-392]
- **NEW** `backend/tests/test_division_attendance.py` — division-attendance API tests.
- **UPDATE** [backend/tests/test_frontend.py](backend/tests/test_frontend.py) — assert the division-breakdown control renders. [Source: backend/tests/test_frontend.py:43-49]

### Dates — keep it simple and JSON-friendly

- Service dates are `datetime.date`, exchanged as ISO strings (e.g. `"2026-07-05"`). Reuse the existing pattern; native `<input type="date">` already exists for service creation — no new UI controls needed for dates. [Source: backend/app/static/index.html:124-125]
- **Avoid `datetime.now()` in tests** — pass explicit dates in payloads so per-service/per-date assertions are stable.

### Testing standards (match existing patterns — non-negotiable for green tests)

- Framework: **pytest** + FastAPI `TestClient`. Tests live in `backend/tests/`; instantiate `client = TestClient(app)` at module top. [Source: backend/tests/test_attendance.py:7-11]
- The autouse `fresh_database` fixture in [backend/tests/conftest.py](backend/tests/conftest.py) drops/creates ALL tables per test and seeds default divisions; the bare `TestClient` does **not** run `lifespan`, so do not rely on startup side effects beyond conftest. New tables aren't needed here, so no fixture change. [Source: backend/tests/conftest.py:17-30]
- Reuse the helper style from `test_attendance.py` (`_household()`, `_division()`, `_member()`, `_service()`) to build fixtures inline. To test multi-division membership, create members with `division_ids: [a, b]` via `POST /members` (already supported). [Source: backend/tests/test_attendance.py:14-37, backend/app/main.py:185-209]
- `lifespan` in main.py must remain `async def`. [Source: backend/app/main.py:134-138]
- Run from the `backend` directory: `python -m pytest -q`. Current baseline is **52 passing** (42 from Epic 1 + 10 from Story 2.1); keep all green and add division-attendance tests.
- `backend/church.db` is gitignored and regenerated by tests — don't commit it.
- Follow red-green-refactor: write failing tests first, then implement minimally, then refactor.

### Architecture compliance

- **AD-1 (single source of truth):** division attendance is computed from existing `AttendanceRecord` + `MemberDivisionLink`; no copied or parallel data. [Source: _bmad-output/implementation-artifacts/architecture-spine.md#AD-1]
- **AD-3 (domain-oriented modules):** stays within the **Attendance Module** in `backend/app`, reading from the Members module's division links. [Source: architecture-spine.md#4-suggested-module-boundaries]
- **AD-4 (workflow-first data entry):** no extra data entry — division breakdown is a derived read shown inline in the existing fast-entry attendance panel. [Source: architecture-spine.md#AD-4]
- **AD-5 (reporting from the same data model):** per-division summaries are reports read straight from the main data model, enabling later dashboards (Epic 4) without a separate store. [Source: architecture-spine.md#AD-5]
- **AD-2 (RBAC):** deferred — no auth layer exists in the baseline and no AC here requires it, consistent with Stories 1.1–2.1. [Source: architecture-spine.md#AD-2]

### Previous Story Intelligence (Story 2.1)

- 2.1 validated services with **404** and members with **400**, validating all ids up front so requests fail atomically. Mirror this. [Source: backend/app/main.py:338-344]
- 2.1 returns explicit read schemas via helpers (`_to_read`, `_present_members`) rather than raw table models — do the same for division counts. [Source: backend/app/main.py:64-79, 392-402]
- 2.1's idempotent recording means a service's present set is well-defined (one row per member+service) — division counts won't double-count from duplicate attendance rows. [Source: backend/app/models.py:160-162]
- 2.1 added the attendance UI additively inside a single `#attendance-panel` card and refreshed derived views after save (`refreshProfileHistory`) — follow that pattern for the division breakdown (refresh after `saveAttendance`). [Source: backend/app/static/index.html:368-406]

### Project Structure Notes

- Modular FastAPI backend: `backend/app/` (`main.py`, `models.py`, `schemas.py`, `database.py`, `static/index.html`) + `backend/tests/`. This story stays within those files plus one new test module. Stack (FastAPI + SQLModel + SQLite + vanilla-JS SPA) is already in place — **no new dependencies required**.
- This is the second story of Epic 2 (Attendance). It is **purely additive** on top of Story 2.1's model; the next story (2.3 Manage event RSVPs) introduces new `Event`/`EventRSVP` entities and is out of scope here.

### References

- [Source: _bmad-output/planning-artifacts/epics-and-stories.md#story-22-track-attendance-by-division]
- [Source: _bmad-output/planning-artifacts/developer-ready-stories.md#22-track-attendance-by-division]
- [Source: _bmad-output/implementation-artifacts/2-1-record-attendance-for-services.md] (Attendance module this story extends; forward-compatibility design note)
- [Source: _bmad-output/implementation-artifacts/architecture-spine.md] (AD-1, AD-3, AD-4, AD-5; Attendance Module; Attendance Record / Division concepts)
- [Source: backend/app/models.py] (AttendanceRecord, Service, Member↔Division link — the data this story aggregates)
- [Source: backend/app/main.py] (attendance endpoint + validation patterns to mirror; `func`/`select` already imported)
- [Source: backend/tests/test_attendance.py] (test helper + assertion style to mirror)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m]

### Debug Log References

- `pytest -q` (backend): 62 passed (52 pre-existing + 10 new).
- Red-green-refactor confirmed: the 8 new division-attendance backend tests and 1 new frontend test all failed before implementation (404/AttributeError/missing-control) and passed after. (The 9th backend test — no-mutation — passed in both phases because the new endpoints never write.)
- End-to-end smoke test through the real FastAPI `lifespan`: created two divisions and a member belonging to both, recorded attendance, and verified the by-division breakdown counts the dual-division member in both divisions (Sunday=1, Youth=2), the per-division summaries return correct per-service counts with dates, and the UI serves the `attendance-by-division` control.

### Completion Notes List

- **Read-side only, no schema change (AC #4):** Division attendance is computed entirely from the existing `AttendanceRecord` + `Member.divisions` (`MemberDivisionLink`). No column added to `AttendanceRecord`, no new table — exactly as Story 2.1's forward-compatibility note anticipated. Upholds AD-1/AD-5.
- **Endpoints (AC #1–#3):** Added `GET /services/{id}/attendance/by-division` (present-member counts per division, 404 on unknown service) and `GET /divisions/{id}/attendance` (per-service summary with present counts, 400 on unknown division). Validation messages/status codes match the existing attendance/division conventions in `main.py`.
- **Multi-division members:** A present member counts toward every division they belong to, so a member in both Sunday School and Youth is reflected in both — verified by `test_by_division_member_in_two_divisions_counts_in_both` and the smoke test. Uses the many-to-many link, not the legacy scalar `division_id`.
- **Divisions with no attendance:** Omitted from the by-division breakdown; a division with no attendance returns `[]` from its summary endpoint (no invented zero rows).
- **UI (AC #6):** Added an "Attendance by division" breakdown region (`#attendance-by-division`) inside the existing Record Attendance card. `loadByDivision()` fetches via the existing `api()` helper and renders `division name: count`; it refreshes on service-select change, after `loadAttendance`, and after `saveAttendance`. Purely additive — the existing create/checklist/save flow is unchanged. No new libraries.
- **Regression safety (AC #5):** All 52 prior tests still pass; the new endpoints are read-only and a dedicated test confirms member count/fields are unchanged and the Story 2.1 per-service attendance endpoint still returns present members. RBAC (AD-2) remains deferred, consistent with Epic 1 and Story 2.1.

### File List

- backend/app/schemas.py (modified — added `DivisionAttendanceCount`, `DivisionAttendanceSummaryEntry`)
- backend/app/main.py (modified — imported the two new schemas; added `_division_counts` helper, `GET /services/{id}/attendance/by-division`, `GET /divisions/{id}/attendance`)
- backend/app/static/index.html (modified — `#attendance-by-division` breakdown region; `loadByDivision()`; refresh on service-change / after load / after save)
- backend/tests/test_division_attendance.py (new — 10 tests: per-division counts, dual-division member, exclude empty divisions, invalid service 404, per-division summary, empty summary, invalid division 404, cross-division comparison, primary-division-change visibility regression, no member mutation)
- backend/tests/test_frontend.py (modified — added division-breakdown control test)

## Change Log

- 2026-06-30: Implemented Story 2.2. Added division-attendance as read-side aggregation over the existing Story 2.1 model (no schema change): `GET /services/{id}/attendance/by-division` (present counts per division, dual-division members counted in each) and `GET /divisions/{id}/attendance` (per-service summary with present counts). Surfaced an "Attendance by division" breakdown in the Record Attendance UI. Added 10 tests (now 62 passing). Status → review.
- 2026-06-30: Addressed code review findings — 3 items resolved (now 63 passing):
  - [High] `update_member`: a primary-`division_id` change without `division_ids` no longer leaves the member out of the `MemberDivisionLink` table, so they stay visible to division-based reads (attendance-by-division). Added regression test.
  - [Med] `GET /divisions/{id}/attendance` now returns **404** (not 400) for an unknown division, matching the service-not-found convention; updated the corresponding test.
  - [Med] UI: the service `<select>` now falls back to the first option when the prior selection no longer matches (fixes `selectedIndex = -1` on initial load, which left no service selected and the breakdown blank).
