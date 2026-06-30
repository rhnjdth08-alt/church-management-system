---
title: Story 3.2 Track building fundraising campaigns
status: ready-for-dev
created: 2026-06-30
updated: 2026-06-30
baseline_commit: 4eafd177e32d378d91e1218d16427aff8d5490c3
---

# Story 3.2: Track building fundraising campaigns

Status: review

## Story

As a church leader,
I want to track fundraising campaigns for the church building,
so that pledges and contributions are recorded against a campaign and progress toward the target is visible.

## Acceptance Criteria

1. A fundraising campaign can be created for the building project, with a name, a target amount, and optional description.
2. Pledges can be recorded against a campaign (a commitment to give, by a member/household), with an amount.
3. Contributions can be recorded against a campaign — reusing the existing `Donation` model by linking it to the campaign via the `campaign_id` hook from Story 3.1 (do NOT create a parallel donation store, AD-1/AD-5).
4. Progress toward the campaign target is visible in a summary: target, total pledged, total contributed (raised), and remaining/percent.
5. The UI lets a leader create a campaign, record a pledge, and see progress. Existing functionality unchanged; all existing tests pass.

## Tasks / Subtasks

- [ ] Models (AC: #1, #2, #3) — [backend/app/models.py](backend/app/models.py)
  - [ ] `FundraisingCampaign` (id, name, target_amount float, optional description).
  - [ ] `Pledge` (id, campaign_id FK, amount float, optional member_id/household_id FKs).
  - [ ] `Donation.campaign_id` already exists (nullable, from 3.1) — now used to attribute contributions. No change to `Donation` needed.
- [ ] Schemas — [backend/app/schemas.py](backend/app/schemas.py)
  - [ ] `CampaignCreate`/`CampaignRead`; `PledgeCreate`/`PledgeRead`; `CampaignProgress` (campaign_id, name, target, total_pledged, total_raised, remaining, percent_raised).
- [ ] Endpoints — [backend/app/main.py](backend/app/main.py)
  - [ ] `POST /campaigns` (validate target > 0, name non-empty) + `GET /campaigns`.
  - [ ] `POST /campaigns/{id}/pledges` (validate campaign 404, amount > 0, optional member/household 400) + `GET /campaigns/{id}/pledges`.
  - [ ] `GET /campaigns/{id}/progress` (404 if missing): total_pledged = sum(Pledge.amount); total_raised = sum(Donation.amount where campaign_id == id); remaining = max(target - raised, 0); percent_raised = raised/target*100 (guard divide-by-zero — target validated > 0 so safe).
  - [ ] Donations are linked to a campaign via the existing `POST /donations` with `campaign_id` (already supported by 3.1's schema). Optionally validate `campaign_id` exists when provided (add a 400 check in `create_donation` — see Dev Notes).
- [ ] UI (AC: #5) — [backend/app/static/index.html](backend/app/static/index.html)
  - [ ] "Fundraising" card (`id="fundraising-panel"`): create campaign (name + target), record pledge, show progress (raised/target + percent). Stable ids: `campaign-name`, `campaign-target`, `fundraising-panel`. Reuse `api()`/`$()`.
- [ ] Tests — NEW `backend/tests/test_fundraising.py`; UPDATE [backend/tests/test_frontend.py](backend/tests/test_frontend.py) (`id="fundraising-panel"`).
  - [ ] create/list campaign; reject target <= 0; record pledge; reject pledge to invalid campaign 404; pledge amount <= 0 → 400; contribution via `POST /donations` with campaign_id; progress math (target, pledged, raised, remaining, percent); donation with unknown campaign_id → 400.

## Dev Notes

- **Reuse Donation for contributions (AC #3):** the `campaign_id` column added in Story 3.1 is the contribution link. `total_raised` is `sum(Donation.amount where campaign_id == campaign)`. This keeps a single giving store (AD-1/AD-5). [Source: backend/app/models.py Donation.campaign_id; Story 3.1]
- **Validate campaign_id on donation:** now that campaigns exist, extend `create_donation` to 400 if `campaign_id` is provided but no such campaign — mirrors existing FK validation. This is a small, safe addition to an existing endpoint; keep all prior donation tests green. [Source: backend/app/main.py create_donation]
- **Money/progress:** floats; `percent_raised = total_raised / target_amount * 100`. Target validated `> 0` so no divide-by-zero. Round in the UI, not the API (return raw floats).
- **Patterns/testing:** SQLModel tables + read schemas + `Depends(get_session)` + `session.get` FK validation; pytest + `TestClient` + autouse `fresh_database`; baseline **86 passing**. [Source: backend/app/main.py, backend/tests/conftest.py]

### Architecture compliance

- **AD-1/AD-5:** contributions reuse `Donation`; progress read from the same data. **AD-3:** Giving Module. **AD-4:** fast pledge entry. **AD-2:** RBAC deferred. [Source: _bmad-output/implementation-artifacts/architecture-spine.md]

### References

- [Source: _bmad-output/planning-artifacts/epics-and-stories.md#story-32-track-building-fundraising-campaigns]
- [Source: _bmad-output/planning-artifacts/developer-ready-stories.md#32-track-building-fundraising-campaigns]
- [Source: backend/app/models.py] (Donation.campaign_id); [Source: backend/app/main.py] (validation patterns)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m]

### Debug Log References

- `pytest -q` (backend): 97 passed (86 prior + 11 new). Red-green confirmed.

### Completion Notes List

- **Models:** `FundraisingCampaign` (name, target_amount, description) + `Pledge` (campaign_id FK, amount, optional member/household). Contributions reuse `Donation.campaign_id` (no parallel store, AD-1/AD-5).
- **Endpoints:** `POST/GET /campaigns`; `POST/GET /campaigns/{id}/pledges`; `GET /campaigns/{id}/progress` (target, total_pledged, total_raised, remaining clamped ≥ 0, percent_raised). Extended `create_donation` to 400 on an unknown `campaign_id`.
- **UI:** "Fundraising" card — create campaign, record pledge, live progress line (raised/target/percent/remaining).
- **Regression:** all 86 prior tests pass; the new donation campaign-validation didn't break existing donation tests (they don't send campaign_id).

### File List

- backend/app/models.py (modified — `FundraisingCampaign`, `Pledge`)
- backend/app/schemas.py (modified — `CampaignCreate/Read`, `PledgeCreate/Read`, `CampaignProgress`)
- backend/app/main.py (modified — campaign imports; `campaign_id` validation in create_donation; `POST/GET /campaigns`, pledges, progress)
- backend/app/static/index.html (modified — Fundraising card; `loadFundraising`/`loadProgress`/`createCampaign`/`savePledge`; listeners + init)
- backend/tests/test_fundraising.py (new — 10 tests)
- backend/tests/test_frontend.py (modified — fundraising panel control test)

## Change Log

- 2026-06-30: Implemented Story 3.2 (Track building fundraising campaigns). Added `FundraisingCampaign` + `Pledge`; contributions reuse `Donation.campaign_id`; progress endpoint reports target/pledged/raised/remaining/percent. Fundraising UI card. 11 tests added (97 passing). Status → review.
