---
title: Story 4.1 Send targeted announcements
status: review
created: 2026-06-30
updated: 2026-06-30
baseline_commit: 217dfffd6ac88c93e1a300e5a3abbe6dfa9487d1
---

# Story 4.1: Send targeted announcements

Status: review

## Story

As a staff member,
I want to compose an announcement and send it to a selected group of members,
so that members receive timely updates and the communication is logged.

## Acceptance Criteria

1. A message (subject + body) can be composed and "sent" to a selected audience.
2. The audience can be filtered by ministry tag, division, or household (any combination; empty = all members).
3. The send is logged: each announcement records its subject, body, audience filter, recipient count, and a sent timestamp date; sent announcements are listable.
4. The audience is resolved from the shared `Member` data (AD-1) — reuse the directory filtering logic from Story 1.3, do not re-implement it.
5. No external email/SMS integration exists in this stack; "send" means recording the announcement and resolving recipients (a log + count). This is explicit and acceptable for the MVP.
6. The UI lets a staff member compose an announcement, choose audience filters, preview the recipient count, send, and see the log. Existing functionality unchanged; all existing tests pass.

## Tasks / Subtasks

- [ ] Models (AC: #3) — [backend/app/models.py](backend/app/models.py)
  - [ ] `Announcement` (id, subject, body, date sent, recipient_count int, and the audience filter fields: tag_id/division_id/household_id, status — all nullable).
- [ ] Schemas — [backend/app/schemas.py](backend/app/schemas.py)
  - [ ] `AnnouncementCreate` (subject, body, optional tag_id/division_id/household_id/status, optional date — default not allowed via now(); require date in payload for determinism OR accept optional and document). `AnnouncementRead` (all + id + recipient_count).
- [ ] Endpoints — [backend/app/main.py](backend/app/main.py)
  - [ ] `POST /announcements`: validate subject/body non-empty (400); resolve the audience by reusing the member-filtering query (refactor Story 1.3's filter into a helper `_filter_members(session, ...)` used by both `GET /members` and this endpoint); store recipient_count = len(resolved); return `AnnouncementRead`.
  - [ ] `GET /announcements`: list logged announcements (most recent first acceptable).
  - [ ] `GET /announcements/preview`: same filters as POST but returns just `{ "recipient_count": N }` without logging (for the UI preview).
- [ ] UI (AC: #6) — [backend/app/static/index.html](backend/app/static/index.html)
  - [ ] "Announcements" card (`id="announcements-panel"`): subject, body, audience filter selects (tag/division/household), a live recipient-count preview, Send button, and a log list. Stable ids: `announcement-subject`, `announcement-body`, `announcements-panel`. Reuse `api()`/`$()`.
- [ ] Tests — NEW `backend/tests/test_announcements.py`; UPDATE [backend/tests/test_frontend.py](backend/tests/test_frontend.py) (`id="announcements-panel"`).
  - [ ] send to all (no filter) → recipient_count == total members; filter by tag/division/household narrows count; reject empty subject/body; log lists sent announcements; preview returns count without creating a log entry; resolved audience reuses Story 1.3 semantics (AND of filters).

## Dev Notes

- **Reuse directory filtering (AC #4):** `GET /members` (Story 1.3) already filters by household_id/status/division_id/tag_id with AND semantics and a `q` search. Factor that `select(Member)...where(...)` chain into a helper `_filter_members(session, *, q, household_id, status, division_id, tag_id)` returning a list, and call it from both `list_members` and the announcement audience resolution. Refactor must not change `GET /members` behavior — keep all Story 1.3 tests green. [Source: backend/app/main.py list_members]
- **"Send" semantics (AC #5):** no transport layer; recording + counting recipients is the deliverable. Make this explicit in the model/docstring so it isn't mistaken for an actual email send. [Source: architecture-spine.md Communications Module — no transport specified]
- **Determinism in tests:** the announcement carries a `date`; require it in the request payload (like services/events) so tests assert stable values — do NOT use `datetime.now()`. [Source: prior stories' date handling]
- **Patterns/testing:** SQLModel table + read schema + `Depends(get_session)`; pytest + `TestClient` + autouse `fresh_database`; baseline **104 passing**. [Source: backend/tests/conftest.py]

### Architecture compliance

- **AD-1** audience from shared members; **AD-3** Communications Module; **AD-4** fast compose/send; **AD-5** sent log readable for reporting (Story 4.3 export can include it); **AD-2** RBAC deferred. [Source: _bmad-output/implementation-artifacts/architecture-spine.md]

### References

- [Source: _bmad-output/planning-artifacts/epics-and-stories.md#story-41-send-announcements]
- [Source: _bmad-output/planning-artifacts/developer-ready-stories.md#41-send-targeted-announcements]
- [Source: backend/app/main.py list_members] (filter logic to factor + reuse)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m]

### Debug Log References

- `pytest -q` (backend): 112 passed (104 prior + 8 new). The `list_members` filter refactor kept all Story 1.3 search/filter + directory tests green.

### Completion Notes List

- **Model:** `Announcement` (subject, body, date, recipient_count, audience filter fields tag_id/division_id/household_id/status). No transport — "send" records the message + resolved count (AC #5).
- **Refactor (no behavior change):** factored Story 1.3's member filtering into `_filter_members(session, *, q, household_id, status, division_id, tag_id)`, now shared by `GET /members` and announcement audience resolution (AC #4, DRY).
- **Endpoints:** `POST /announcements` (validates subject/body, resolves + stores recipient_count); `GET /announcements` (log, newest first); `GET /announcements/preview` (recipient count for filters, no log entry).
- **UI:** "Announcements" card — subject/body, audience filters (division/tag/household) with a live recipient-count preview, Send, and a sent log.
- **Regression:** all 104 prior tests pass.

### File List

- backend/app/models.py (modified — `Announcement` table)
- backend/app/schemas.py (modified — `AnnouncementCreate`, `AnnouncementRead`, `RecipientCount`)
- backend/app/main.py (modified — announcement imports; `_filter_members` refactor; `_resolve_audience_count`; `POST/GET /announcements`, `GET /announcements/preview`)
- backend/app/static/index.html (modified — Announcements card; `loadAnnouncements`/`previewAudience`/`refreshAnnouncementLog`/`sendAnnouncement`; listeners + init)
- backend/tests/test_announcements.py (new — 8 tests)
- backend/tests/test_frontend.py (modified — announcements panel control test)

## Change Log

- 2026-06-30: Implemented Story 4.1 (Send targeted announcements). Added the Communications Module — `Announcement` log with audience filters reusing the directory's member filtering (factored into `_filter_members`). Endpoints for send/list/preview; an Announcements UI card with live recipient preview. 8 tests added (112 passing). Status → review.
