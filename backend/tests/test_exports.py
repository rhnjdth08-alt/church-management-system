"""Tests for CSV summary exports (Story 4.3, AC #1-#5).

Exports are generated from the shared data model (reusing the dashboard/summary
helpers) and returned as downloadable CSV.
"""

import csv
import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household():
    return client.post("/households", json={"name": "Exp Household"}).json()["id"]


def _division():
    return client.post("/divisions", json={"name": "Exp Division"}).json()["id"]


def _member():
    return client.post(
        "/members",
        json={
            "first_name": "Ex",
            "last_name": "Port",
            "household_id": _household(),
            "division_id": _division(),
        },
    ).json()["id"]


def _rows(text):
    return list(csv.reader(io.StringIO(text)))


def _assert_csv(resp, filename):
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]
    assert filename in resp.headers["content-disposition"]


# --- attendance export ------------------------------------------------------


def test_attendance_export_header_only_when_empty():
    resp = client.get("/exports/attendance.csv")
    _assert_csv(resp, "attendance")
    rows = _rows(resp.text)
    assert rows[0] == ["service_id", "name", "date", "present"]
    assert len(rows) == 1  # header only


def test_attendance_export_includes_service():
    m = _member()
    svc = client.post("/services", json={"name": "Sunday", "date": "2026-07-05"}).json()
    client.post(f"/services/{svc['id']}/attendance", json={"member_ids": [m]})
    resp = client.get("/exports/attendance.csv")
    _assert_csv(resp, "attendance")
    rows = _rows(resp.text)
    data = rows[1:]
    assert any(r[1] == "Sunday" and r[3] == "1" for r in data)


# --- giving export ----------------------------------------------------------


def test_giving_export_includes_period():
    m = _member()
    client.post(
        "/donations",
        json={"amount": 100.0, "date": "2026-07-01", "donation_type": "tithe", "member_id": m},
    )
    resp = client.get("/exports/giving.csv")
    _assert_csv(resp, "giving")
    rows = _rows(resp.text)
    assert rows[0] == ["period", "total", "count"]
    assert any(r[0] == "2026-07" and float(r[1]) == 100.0 for r in rows[1:])


# --- fundraising export -----------------------------------------------------


def test_fundraising_export_includes_campaign():
    c = client.post("/campaigns", json={"name": "Build", "target_amount": 1000.0}).json()
    m = _member()
    client.post(
        "/donations",
        json={"amount": 250.0, "date": "2026-07-01", "donation_type": "building", "member_id": m, "campaign_id": c["id"]},
    )
    resp = client.get("/exports/fundraising.csv")
    _assert_csv(resp, "fundraising")
    rows = _rows(resp.text)
    assert rows[0] == [
        "campaign_id", "name", "target", "total_pledged", "total_raised", "remaining", "percent_raised",
    ]
    data_row = next(r for r in rows[1:] if r[1] == "Build")
    assert float(data_row[4]) == 250.0  # total_raised


def test_csv_formula_injection_is_neutralized():
    """A campaign name beginning with a formula trigger is prefixed with ' so a
    spreadsheet treats it as text, not an executable formula."""
    client.post("/campaigns", json={"name": "=SUM(A1:A9)", "target_amount": 100.0})
    rows = _rows(client.get("/exports/fundraising.csv").text)
    name_cell = next(r[1] for r in rows[1:] if "SUM(A1:A9)" in r[1])
    assert name_cell.startswith("'=")  # neutralized, not a live formula
