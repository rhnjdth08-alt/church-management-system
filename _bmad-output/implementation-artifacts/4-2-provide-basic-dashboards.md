---
title: Story 4.2 Provide basic dashboards
status: review
created: 2026-06-30
updated: 2026-06-30
baseline_commit: bc2fdf9457e920d2e8b5a834ed627c102855a7d7
---

# Story 4.2: Provide basic dashboards

Status: review

## Story

As a leader,
I want a dashboard with key metrics for attendance, giving, and fundraising,
so that I can see the church's health at a glance.

## Acceptance Criteria

1. A dashboard shows headline metrics: total members, total services, total attendance records, total events, total giving, and number of campaigns.
2. It shows attendance trend by service (each service with its present count) and giving trend by month (reuse Story 3.3 by-period).
3. It shows fundraising progress for all campaigns (reuse Story 3.3 all-campaigns progress).
4. All metrics are computed from the shared data model (AD-5) — no separate store; reuse existing helpers/endpoints where possible.
5. The UI shows a Dashboard card with the headline numbers and trends. Existing functionality unchanged; all existing tests pass.

## Tasks / Subtasks

- [ ] Schemas — [backend/app/schemas.py](backend/app/schemas.py)
  - [ ] `ServiceAttendanceCount` (service_id, name, date, present).
  - [ ] `DashboardSummary` (member_count, service_count, attendance_count, event_count, campaign_count, total_giving, giving_by_period: list[GivingByPeriod], attendance_by_service: list[ServiceAttendanceCount], campaigns: list[CampaignProgress]).
- [ ] Endpoints — [backend/app/main.py](backend/app/main.py)
  - [ ] `GET /dashboard` → `DashboardSummary`. Counts via `select(func.count())`/`len`. Reuse: giving_by_period from the same grouping as `giving_summary` (factor `_giving_by_period(session)` so both share it); campaign progress via `_campaign_progress`; attendance per service via the existing `_present_members` (count length per service).
- [ ] UI (AC: #5) — [backend/app/static/index.html](backend/app/static/index.html)
  - [ ] "Dashboard" card (`id="dashboard-panel"`): headline metric tiles + attendance-by-service list + giving-by-month list + campaign progress. A refresh button (`id="refresh-dashboard"`). Reuse `api()`/`$()`.
- [ ] Tests — NEW `backend/tests/test_dashboard.py`; UPDATE [backend/tests/test_frontend.py](backend/tests/test_frontend.py) (`id="dashboard-panel"`).
  - [ ] counts reflect created members/services/events/campaigns/donations; total_giving sums donations; attendance_by_service present counts correct; giving_by_period matches; campaigns list matches; empty system → all zeros/empty lists.

## Dev Notes

- **Reuse, don't duplicate (AC #4):** the giving-by-period grouping in `giving_summary` should be factored into `_giving_by_period(session) -> list[GivingByPeriod]`, then called by both `giving_summary` and `/dashboard` (keep `GET /giving/summary` behavior identical — Story 3.3 tests must stay green). Campaign progress reuses `_campaign_progress`. Attendance-per-service reuses `_present_members` (its length). [Source: backend/app/main.py giving_summary, _campaign_progress, _present_members]
- **Counts:** `session.exec(select(func.count()).select_from(Model)).one()` or `len(session.exec(select(Model)).all())` — either is fine at this scale. `func` is already imported. [Source: backend/app/main.py imports]
- **Patterns/testing:** read schema + `Depends(get_session)`; pytest + `TestClient` + autouse `fresh_database`; explicit dates; baseline **112 passing**. [Source: backend/tests/conftest.py]

### Architecture compliance

- **AD-5** all dashboard data from the main model; **AD-3** Reporting Module; **AD-2** RBAC deferred. [Source: _bmad-output/implementation-artifacts/architecture-spine.md]

### References

- [Source: _bmad-output/planning-artifacts/developer-ready-stories.md#42-provide-basic-dashboards]
- [Source: backend/app/main.py] (giving_summary, _campaign_progress, _present_members to reuse)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m]

### Debug Log References

- `pytest -q` (backend): 117 passed (112 prior + 5 new). The `_giving_by_period` refactor kept all Story 3.3 giving-summary tests green.

### Completion Notes List

- **Endpoint:** `GET /dashboard` → headline counts (members, services, attendance records, events, campaigns), total_giving, plus attendance-by-service, giving-by-month, and all-campaign progress.
- **Reuse (AC #4):** factored `_giving_by_period(session)` out of `giving_summary` (shared by 3.3 and the dashboard); reused `_campaign_progress` and `_present_members`. No new aggregation logic duplicated.
- **UI:** "Dashboard" card — metric lines + attendance/giving/campaign trend lists, with a Refresh button. Added a small `renderList` helper.
- **Read-only:** all 112 prior tests pass.

### File List

- backend/app/schemas.py (modified — `ServiceAttendanceCount`, `DashboardSummary`)
- backend/app/main.py (modified — dashboard imports; `_giving_by_period` refactor; `GET /dashboard`)
- backend/app/static/index.html (modified — Dashboard card; `loadDashboard`/`renderList`; refresh listener + init)
- backend/tests/test_dashboard.py (new — 4 tests)
- backend/tests/test_frontend.py (modified — dashboard panel control test)

## Change Log

- 2026-06-30: Implemented Story 4.2 (Provide basic dashboards). Added `GET /dashboard` aggregating member/service/attendance/event/campaign counts, total giving, and attendance/giving/campaign trends — all reusing existing helpers. Dashboard UI card. 5 tests added (117 passing). Status → review.
