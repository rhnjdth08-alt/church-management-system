---
title: Story 3.3 Review giving summaries
status: review
created: 2026-06-30
updated: 2026-06-30
baseline_commit: ae6e3209d474914985985d280b08fceaf58a44ad
---

# Story 3.3: Review giving summaries

Status: review

## Story

As a church leader,
I want to review giving summaries and see fundraising progress alongside them,
so that I can monitor stewardship trends.

## Acceptance Criteria

1. A summary view shows giving totals by period (e.g. by month) and by donor (member).
2. The summary is computed from the shared `Donation` data (AD-5) — no separate store.
3. Fundraising campaign progress can be viewed alongside the general giving summary (reuse Story 3.2's progress per campaign).
4. The UI surfaces a giving summary (totals by period and top donors) and the fundraising progress for campaigns.
5. Read-only: existing functionality unchanged; all existing tests pass.

## Tasks / Subtasks

- [ ] Schemas — [backend/app/schemas.py](backend/app/schemas.py)
  - [ ] `GivingByPeriod` (period: str "YYYY-MM", total: float, count: int).
  - [ ] `GivingByDonor` (member_id: int, total: float, count: int).
  - [ ] `GivingSummary` (grand_total: float, by_period: list[GivingByPeriod], by_donor: list[GivingByDonor]).
- [ ] Endpoints — [backend/app/main.py](backend/app/main.py)
  - [ ] `GET /giving/summary` → `GivingSummary`: grand_total = sum all donations; by_period grouped by `YYYY-MM` of donation date; by_donor grouped by member_id (donations with a member_id only; household-only gifts excluded from per-donor but included in grand_total). Deterministic ordering (period ascending; donor by member_id).
  - [ ] `GET /giving/campaigns/progress` → `list[CampaignProgress]`: progress for every campaign (reuse the per-campaign computation from Story 3.2 — factor a helper so it isn't duplicated).
- [ ] UI (AC: #4) — [backend/app/static/index.html](backend/app/static/index.html)
  - [ ] "Giving Summary" card (`id="summary-panel"`): show grand total, totals by period, top donors, and per-campaign progress. A "Refresh summary" button (`id="refresh-summary"`). Reuse `api()`/`$()`.
- [ ] Tests — NEW `backend/tests/test_giving_summary.py`; UPDATE [backend/tests/test_frontend.py](backend/tests/test_frontend.py) (`id="summary-panel"`).
  - [ ] grand total across mixed member/household donations; by-period grouping (two months); by-donor grouping (two members); empty summary returns zeros/empty lists; campaigns progress endpoint returns one entry per campaign with correct raised totals.

## Dev Notes

- **Reporting from the same data (AC #2, AD-5):** read straight from `Donation`. Period key = `donation.date.strftime("%Y-%m")` (date is a `datetime.date`). Group in Python (dataset is small; avoids DB-specific date functions). [Source: backend/app/models.py Donation]
- **Reuse 3.2 progress (AC #3):** the per-campaign progress math in `campaign_progress` should be factored into a helper (e.g. `_campaign_progress(session, campaign)`) and called by both the existing `GET /campaigns/{id}/progress` and the new `GET /giving/campaigns/progress`. Refactor without changing existing behavior (existing fundraising tests must stay green). [Source: backend/app/main.py campaign_progress]
- **Donor scope:** by_donor covers donations with a `member_id`. Household-only gifts still count in `grand_total` and `by_period`. Document this so the numbers reconcile.
- **Patterns/testing:** read schemas + `Depends(get_session)`; pytest + `TestClient` + autouse `fresh_database`; explicit dates; baseline **97 passing**. [Source: backend/tests/conftest.py]

### Architecture compliance

- **AD-5** reporting from the main data model; **AD-3** Reporting/Giving cohesion; **AD-2** RBAC deferred. [Source: _bmad-output/implementation-artifacts/architecture-spine.md]

### References

- [Source: _bmad-output/planning-artifacts/epics-and-stories.md#story-33-review-giving-summaries]
- [Source: _bmad-output/planning-artifacts/developer-ready-stories.md#33-display-giving-and-fundraising-summaries]
- [Source: backend/app/main.py campaign_progress] (to factor + reuse)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m]

### Debug Log References

- `pytest -q` (backend): 104 passed (97 prior + 7 new). Refactor of campaign progress kept all 10 fundraising tests green.

### Completion Notes List

- **Endpoints:** `GET /giving/summary` (grand_total, by_period grouped by `YYYY-MM`, by_donor grouped by member_id; household-only gifts in totals but not per-donor); `GET /giving/campaigns/progress` (progress for every campaign).
- **Refactor (no behavior change):** factored per-campaign math into `_campaign_progress(session, campaign)`, now shared by `GET /campaigns/{id}/progress` and the all-campaigns endpoint (AC #3, DRY).
- **UI:** "Giving Summary" card — grand total, totals by month, top donors (desc, top 10), and per-campaign progress, with a Refresh button.
- **Read-only (AC #5):** all 97 prior tests pass; nothing mutates data.

### File List

- backend/app/schemas.py (modified — `GivingByPeriod`, `GivingByDonor`, `GivingSummary`)
- backend/app/main.py (modified — summary imports; `_campaign_progress` helper refactor; `GET /giving/summary`, `GET /giving/campaigns/progress`)
- backend/app/static/index.html (modified — Giving Summary card; `loadSummary`; refresh listener + init)
- backend/tests/test_giving_summary.py (new — 6 tests)
- backend/tests/test_frontend.py (modified — summary panel control test)

## Change Log

- 2026-06-30: Implemented Story 3.3 (Review giving summaries). Added giving summary (by period + by donor) and all-campaigns progress, both read from existing Donation/campaign data. Factored shared campaign-progress helper. Giving Summary UI card. 7 tests added (104 passing). Status → review.
