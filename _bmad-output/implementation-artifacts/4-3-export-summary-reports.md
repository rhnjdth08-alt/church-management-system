---
title: Story 4.3 Export summary reports
status: review
created: 2026-06-30
updated: 2026-06-30
baseline_commit: 419050cb5c8139a87e11d894f2acf1f5e0588e89
---

# Story 4.3: Export summary reports

Status: review

## Story

As a staff member,
I want to export summary reports,
so that leadership can review attendance, giving, and fundraising outside the app.

## Acceptance Criteria

1. Reports can be exported to CSV (a downloadable file with the correct content type and a filename).
2. Export content covers attendance (by service), giving (by month), and fundraising (campaign progress) summaries.
3. Exports are generated from the shared data model (AD-5) — reuse the existing summary/dashboard helpers; no separate store.
4. PDF is out of scope for the MVP (would require a new dependency the lean stack avoids) — CSV is the deliverable. This is explicit.
5. The UI offers download links/buttons for each export. Existing functionality unchanged; all existing tests pass.

## Tasks / Subtasks

- [ ] Endpoints — [backend/app/main.py](backend/app/main.py)
  - [ ] `GET /exports/attendance.csv` → CSV of attendance-by-service (columns: service_id, name, date, present). Reuse `_present_members`/service list (same as dashboard).
  - [ ] `GET /exports/giving.csv` → CSV of giving-by-month (columns: period, total, count). Reuse `_giving_by_period`.
  - [ ] `GET /exports/fundraising.csv` → CSV of campaign progress (columns: campaign_id, name, target, total_pledged, total_raised, remaining, percent_raised). Reuse `_campaign_progress`.
  - [ ] Each returns `Response(content=csv_text, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=...csv"})`. Build CSV with the stdlib `csv` module + `io.StringIO` (no new dependency).
- [ ] UI (AC: #5) — [backend/app/static/index.html](backend/app/static/index.html)
  - [ ] Add export links to the Dashboard card (`id="exports"` region): anchor tags / buttons linking to the three CSV endpoints (with `download`). Stable id: `export-attendance`, `export-giving`, `export-fundraising`.
- [ ] Tests — NEW `backend/tests/test_exports.py`; UPDATE [backend/tests/test_frontend.py](backend/tests/test_frontend.py) (`id="exports"`).
  - [ ] each endpoint returns 200 with `text/csv` content type and a `Content-Disposition` attachment header; CSV header row present; a created service/donation/campaign appears as a data row; empty system returns just the header row.

## Dev Notes

- **CSV via stdlib (AC #1, #4):** `import csv, io`; write rows into `io.StringIO()` with `csv.writer`; return its `getvalue()` in a FastAPI `Response`. No reportlab/pandas — keep the lean stack. [Source: architecture-spine.md no-new-deps posture]
- **Reuse helpers (AC #3):** attendance rows from the same per-service present counts the dashboard uses; giving rows from `_giving_by_period`; fundraising rows from `_campaign_progress` over all campaigns. Do not recompute. [Source: backend/app/main.py dashboard, _giving_by_period, _campaign_progress, _present_members]
- **Response import:** `from fastapi import Response` — `FileResponse` is already imported from `fastapi.responses`; add `Response` from `fastapi`. [Source: backend/app/main.py imports]
- **Content type assertion:** TestClient response `.headers["content-type"]` will start with `text/csv`. Assert `startswith` to tolerate charset suffix.
- **Patterns/testing:** pytest + `TestClient` + autouse `fresh_database`; explicit dates; baseline **117 passing**. [Source: backend/tests/conftest.py]

### Architecture compliance

- **AD-5** exports from the main data model; **AD-3** Reporting Module; **AD-2** RBAC deferred. [Source: _bmad-output/implementation-artifacts/architecture-spine.md]

### References

- [Source: _bmad-output/planning-artifacts/developer-ready-stories.md#43-export-summary-reports]
- [Source: backend/app/main.py] (dashboard/summary helpers to reuse)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m]

### Debug Log References

- `pytest -q` (backend): 122 passed (117 prior + 5 new). Red-green confirmed.
- Smoke test through lifespan: all three endpoints return `text/csv` with an attachment header and correct data rows (attendance `1,Svc,2026-07-05,1`; giving `2026-07,250.0,1`; fundraising `1,Build,1000.0,0.0,250.0,750.0,25.0`).

### Completion Notes List

- **Endpoints:** `GET /exports/attendance.csv`, `/exports/giving.csv`, `/exports/fundraising.csv` — each a downloadable CSV (`text/csv` + `Content-Disposition: attachment`).
- **Stdlib only (AC #4):** `_csv_response` builds CSV with the `csv` module + `io.StringIO`; no new dependency. PDF intentionally out of scope.
- **Reuse (AC #3):** attendance rows from `_present_members` per service; giving rows from `_giving_by_period`; fundraising rows from `_campaign_progress`. No recomputation.
- **UI:** three `download` anchor links in the Dashboard card (`#exports` region) — the browser handles the download, no JS.
- **Read-only:** all 117 prior tests pass.

### File List

- backend/app/main.py (modified — `csv`/`io`/`Response` imports; `_csv_response` helper; three `/exports/*.csv` endpoints)
- backend/app/static/index.html (modified — Export reports links in Dashboard card)
- backend/tests/test_exports.py (new — 4 tests)
- backend/tests/test_frontend.py (modified — exports links control test)

## Change Log

- 2026-06-30: Implemented Story 4.3 (Export summary reports). Added CSV exports for attendance, giving, and fundraising — generated from existing summary helpers via the stdlib `csv` module (no new dependency). Download links in the Dashboard UI. 5 tests added (122 passing). Completes Epic 4 and the MVP backlog. Status → review.
