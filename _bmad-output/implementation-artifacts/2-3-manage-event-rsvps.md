---
title: Story 2.3 Manage event RSVPs
status: ready-for-dev
created: 2026-06-30
updated: 2026-06-30
baseline_commit: d5022fa137393f963361b1c187bf2a90386759d2
---

# Story 2.3: Manage event RSVPs

Status: review

## Story

As an event coordinator,
I want to create events and track who is attending or not attending,
so that I can see attendee counts and plan events more effectively.

## Acceptance Criteria

1. An event can be created with a date, location, and description (plus a name/title).
2. A member can be marked as attending or not attending a given event (an RSVP), referencing the shared `Member` records (AD-1, no parallel person list).
3. An RSVP is idempotent per member+event: re-RSVPing updates the response rather than creating a duplicate.
4. The list of RSVPs for an event is viewable, and the attendee count (number responding "yes") is visible.
5. Events and RSVPs are a distinct domain from Attendance/Services (the Events Module per AD-3) — do not conflate `Event` with the existing `Service` table.
6. The UI lets a coordinator create an event and RSVP members, showing the yes/no breakdown and attendee count. Existing functionality (members, attendance) is unchanged. All existing tests still pass.

## Tasks / Subtasks

- [ ] Models (AC: #1, #2, #3, #5) — in [backend/app/models.py](backend/app/models.py)
  - [ ] Add `Event` table (id, name, date, location, description) — `location`/`description` optional. Mirror the `Service` table style.
  - [ ] Add `EventRSVP` table (id, member_id FK, event_id FK, response) with `UniqueConstraint(member_id, event_id)` for idempotent RSVP (mirror `AttendanceRecord`). `response` is a string: `"yes"` or `"no"`.
  - [ ] Add relationships (`Event.rsvps` ↔ `EventRSVP.event`).
- [ ] Schemas (AC: #1, #2, #4) — in [backend/app/schemas.py](backend/app/schemas.py)
  - [ ] `EventCreate` (name, date, optional location/description), `EventRead` (id + those fields).
  - [ ] `RSVPCreate` (`member_id: int`, `response: str`), `RSVPRead` (member_id, response), and `EventRSVPSummary` (event_id, yes_count, no_count, total).
- [ ] Endpoints (AC: #1, #2, #3, #4) — in [backend/app/main.py](backend/app/main.py)
  - [ ] `POST /events` + `GET /events` (mirror `POST/GET /services`).
  - [ ] `POST /events/{event_id}/rsvps` — validate event (404 "Event not found.") and member (400 "Member not found."); upsert by (member_id, event_id) so re-RSVP updates `response`; validate `response` is `"yes"`/`"no"` (400 otherwise). Return the updated `EventRSVPSummary`.
  - [ ] `GET /events/{event_id}/rsvps` — list `RSVPRead` for the event (404 if event missing).
  - [ ] `GET /events/{event_id}/summary` — `EventRSVPSummary` with yes/no/total counts (404 if event missing).
- [ ] UI (AC: #6) — in [backend/app/static/index.html](backend/app/static/index.html)
  - [ ] Add an "Events & RSVPs" card (`id="events-panel"`): create event (name + `<input type="date">` + location + description); select an event; per-member yes/no RSVP control; show the attendee count + yes/no breakdown. Reuse `api()`/`$()`/card styling. Stable ids: `event-name`, `event-date`, `events-panel`, `rsvp-summary`.
- [ ] Tests (AC: #1–#6)
  - [ ] NEW `backend/tests/test_events.py`: create/list event; RSVP yes/no; idempotent re-RSVP updates response (no duplicate); invalid event 404 / invalid member 400 / invalid response 400; list rsvps; summary counts; RSVP does not mutate member records.
  - [ ] UPDATE [backend/tests/test_frontend.py](backend/tests/test_frontend.py): assert `id="events-panel"` present.

## Dev Notes

### Reuse established patterns exactly (Epic 1/2 conventions)

- **Models:** `Event` mirrors `Service` (id, name, date + extra optional fields). `EventRSVP` mirrors `AttendanceRecord` (member FK + event FK + `UniqueConstraint(member_id, event_id)`). [Source: backend/app/models.py:138-169]
- **Idempotent upsert:** like `record_attendance`, look up the existing `(member_id, event_id)` row first; if present, update `response`, else insert. Validate member up front (400) and event (404). [Source: backend/app/main.py record_attendance]
- **Schemas/serializers:** explicit read schemas, not raw tables (see `_to_read`, `ServiceRead`). [Source: backend/app/schemas.py]
- **Endpoints:** `session: Session = Depends(get_session)`; `session.get(Model, id)` for FK validation; `select(...)` for queries. New tables auto-register via `main.py`'s `from .models import ...`. [Source: backend/app/main.py]
- **Distinct from Attendance (AC #5):** `Event` is NOT `Service`. RSVP ("will you attend?") differs from attendance ("were you present?"). Keep them separate tables/endpoints. [Source: architecture-spine.md#AD-3 Events Module; #Data Concepts Event / RSVP]

### Testing standards

- pytest + `TestClient(app)` at module top; autouse `fresh_database` fixture drops/creates all tables + seeds divisions (new tables auto-created). Pass explicit dates. Run `python -m pytest -q` from `backend`. Baseline **63 passing** — keep green. [Source: backend/tests/conftest.py, backend/tests/test_attendance.py]

### Architecture compliance

- **AD-1:** RSVPs reference shared `Member` records. **AD-3:** Events Module, cohesive in `backend/app`. **AD-4:** fast RSVP entry (one control per member). **AD-5:** attendee counts read from `EventRSVP`. **AD-2 (RBAC):** deferred, consistent with prior stories. [Source: _bmad-output/implementation-artifacts/architecture-spine.md]

### Files to touch

- UPDATE models.py, schemas.py, main.py, static/index.html; NEW backend/tests/test_events.py; UPDATE backend/tests/test_frontend.py.

### References

- [Source: _bmad-output/planning-artifacts/epics-and-stories.md#story-23-manage-event-rsvps]
- [Source: _bmad-output/planning-artifacts/developer-ready-stories.md#23-manage-event-rsvps]
- [Source: backend/app/models.py] (Service/AttendanceRecord patterns to mirror)
- [Source: backend/app/main.py] (endpoint + idempotent-upsert + FK-validation patterns)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m]

### Debug Log References

- `pytest -q` (backend): 74 passed (63 prior + 11 new). Red-green confirmed.
- Smoke test through lifespan: created an event, RSVP'd yes/no, verified idempotent update (member changed no→yes, total stays 2, no duplicate), and the served UI exposes the events panel.

### Completion Notes List

- **Models:** `Event` (name, date, optional location/description) and `EventRSVP` (member_id, event_id, response) with `UniqueConstraint(member_id, event_id)`. Distinct from `Service`/`AttendanceRecord` (AC #5, AD-3).
- **Endpoints:** `POST/GET /events`; `POST /events/{id}/rsvps` (idempotent upsert by member+event, validates event 404 / member 400 / response 400, returns summary); `GET /events/{id}/rsvps`; `GET /events/{id}/summary` (yes/no/total).
- **UI:** "Events & RSVPs" card — create event, pick event, per-member yes/no radios that POST on change, live attendee summary. Reuses `api()`/`$()`/card styling.
- **Regression (AC #6):** all 63 prior tests still pass; a test confirms RSVP does not mutate member records. RBAC deferred.

### File List

- backend/app/models.py (modified — `Event`, `EventRSVP` tables + relationship)
- backend/app/schemas.py (modified — `EventCreate`, `EventRead`, `RSVPCreate`, `RSVPRead`, `EventRSVPSummary`)
- backend/app/main.py (modified — event/RSVP imports; `POST/GET /events`, `POST/GET /events/{id}/rsvps`, `GET /events/{id}/summary`, `_event_summary` helper)
- backend/app/static/index.html (modified — Events & RSVPs card; `loadEvents`/`loadRsvps`/`sendRsvp`/`createEvent`; listeners + init)
- backend/tests/test_events.py (new — 11 tests)
- backend/tests/test_frontend.py (modified — events panel control test)

## Change Log

- 2026-06-30: Implemented Story 2.3 (Manage event RSVPs). Added the Events Module — `Event` + `EventRSVP` (unique per member+event for idempotent RSVP), `POST/GET /events`, RSVP upsert with yes/no/total summary, and an Events & RSVPs UI card. 11 tests added (74 passing). Status → review.
