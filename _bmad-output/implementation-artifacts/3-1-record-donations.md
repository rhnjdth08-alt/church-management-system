---
title: Story 3.1 Record donations
status: ready-for-dev
created: 2026-06-30
updated: 2026-06-30
baseline_commit: 260c00e16f5703414d30f1c7508d56ee1abf257b
---

# Story 3.1: Record donations

Status: review

## Story

As an administrator,
I want to record donations for a person or household,
so that giving history is maintained and viewable later.

## Acceptance Criteria

1. A donation can be entered for a person (member) or a household, with amount, date, and donation type.
2. Donations reference shared `Member`/`Household` records (AD-1) — no parallel donor list.
3. Donation records can be viewed later: list all donations, and view a member's giving history and a household's giving history.
4. Amount validation: amount must be positive; type is a free-text/category string (e.g. "tithe", "offering", "building").
5. The UI lets an admin record a donation and view giving history. Existing functionality unchanged; all existing tests pass.
6. Forward-compatible: `Donation` carries an optional `campaign_id` (nullable FK, no campaign table yet) so Story 3.2 (fundraising campaigns) can link pledges/contributions without a schema migration. Leave it nullable and unused for now.

## Tasks / Subtasks

- [ ] Models (AC: #1, #2, #6) — [backend/app/models.py](backend/app/models.py)
  - [ ] Add `Donation` table: id, amount (float), date (date), donation_type (str), member_id (nullable FK member.id), household_id (nullable FK household.id), campaign_id (nullable int, NO FK yet — forward-compat for 3.2).
- [ ] Schemas (AC: #1, #3) — [backend/app/schemas.py](backend/app/schemas.py)
  - [ ] `DonationCreate` (amount, date, donation_type, optional member_id, optional household_id, optional campaign_id), `DonationRead` (all fields + id).
- [ ] Endpoints (AC: #1, #3, #4) — [backend/app/main.py](backend/app/main.py)
  - [ ] `POST /donations` — validate amount > 0 (400), donation_type non-empty (400); require at least one of member_id/household_id (400 "A donation must reference a member or household."); validate referenced member (400) / household (400) exist.
  - [ ] `GET /donations` — list all.
  - [ ] `GET /members/{member_id}/donations` — member's giving history (404 if member missing).
  - [ ] `GET /households/{household_id}/donations` — household giving history (404 if household missing).
- [ ] UI (AC: #5) — [backend/app/static/index.html](backend/app/static/index.html)
  - [ ] "Giving" card (`id="giving-panel"`): record a donation (amount + date + type + member select + optional household), list recent donations. Stable ids: `donation-amount`, `donation-date`, `donation-type`, `giving-panel`. Reuse `api()`/`$()`.
- [ ] Tests (AC: #1–#5)
  - [ ] NEW `backend/tests/test_donations.py`: create donation for member; for household; list; member history; household history; reject amount <= 0; reject missing donor; reject invalid member/household; donation does not mutate member records.
  - [ ] UPDATE [backend/tests/test_frontend.py](backend/tests/test_frontend.py): assert `id="giving-panel"`.

## Dev Notes

- **Money:** store `amount` as `float` for SQLite simplicity (consistent with the lean stack — no Decimal column type set up). Validate `> 0`. Accept/return as JSON number. Dates as ISO strings via `datetime.date` (see Service/Event).
- **Donor reference (AC #2):** nullable `member_id` and `household_id`; at least one required. Mirror existing FK validation (`session.get(Model, id)` → 400). [Source: backend/app/main.py member/household validation]
- **Forward-compat campaign_id (AC #6):** a plain nullable `int` column, NOT a FK yet (the campaign table arrives in 3.2). This avoids a migration later while keeping 3.1 self-contained. [Source: architecture-spine.md#AD-5 reporting; Story 3.2/3.3 build on this]
- **Patterns:** SQLModel table + explicit read schema + endpoints with `Depends(get_session)`; new table auto-registers via `main.py` import. [Source: backend/app/models.py, main.py]
- **Testing:** pytest + `TestClient`; autouse `fresh_database`; explicit dates/amounts; baseline **74 passing** — keep green. [Source: backend/tests/conftest.py]

### Architecture compliance

- **AD-1** shared donor records; **AD-3** Giving Module; **AD-4** fast donation entry; **AD-5** giving history read from `Donation` (enables 3.3 summaries); **AD-2** RBAC deferred. [Source: _bmad-output/implementation-artifacts/architecture-spine.md]

### References

- [Source: _bmad-output/planning-artifacts/epics-and-stories.md#story-31-record-donations]
- [Source: _bmad-output/planning-artifacts/developer-ready-stories.md#31-record-donations]
- [Source: backend/app/models.py] (table + FK patterns); [Source: backend/app/main.py] (validation patterns)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m]

### Debug Log References

- `pytest -q` (backend): 86 passed (74 prior + 12 new). Red-green confirmed.

### Completion Notes List

- **Model:** `Donation` (amount, date, donation_type, nullable member_id/household_id FKs, nullable `campaign_id` forward-compat for 3.2 — plain column, no FK yet).
- **Endpoints:** `POST /donations` (validates amount > 0, type non-empty, at least one donor, FK existence); `GET /donations`; `GET /members/{id}/donations`; `GET /households/{id}/donations`.
- **UI:** "Giving" card — record a donation (amount/date/type/member/household) and view recent donations. Reuses `fillSelect`/`api()`/`$()`.
- **Regression (AC #5):** all 74 prior tests pass; a test confirms recording a donation doesn't mutate member records.

### File List

- backend/app/models.py (modified — `Donation` table)
- backend/app/schemas.py (modified — `DonationCreate`, `DonationRead`)
- backend/app/main.py (modified — donation imports; `POST/GET /donations`, member/household donation history)
- backend/app/static/index.html (modified — Giving card; `loadGiving`/`loadDonations`/`saveDonation`; listener + init)
- backend/tests/test_donations.py (new — 11 tests)
- backend/tests/test_frontend.py (modified — giving panel control test)

## Change Log

- 2026-06-30: Implemented Story 3.1 (Record donations). Added the Giving Module foundation — `Donation` referencing shared member/household records, with a nullable `campaign_id` hook for Story 3.2. Endpoints for create/list and per-member/per-household history; a Giving UI card. 12 tests added (86 passing). Status → review.
- 2026-06-30: Code review fixes — donation amount now rejects NaN/inf (a naive `<= 0` check let them through and they poisoned every aggregate); unknown `campaign_id` on a donation now returns 404 to match the pledge endpoint's treatment of the same missing-campaign condition. Regression tests added; the fundraising test asserting the old 400 was updated to 404.
