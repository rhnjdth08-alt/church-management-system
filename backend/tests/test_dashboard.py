"""Tests for the basic dashboard (Story 4.2, AC #1-#5).

The dashboard aggregates headline counts and trends from the shared data model;
no separate store.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household():
    return client.post("/households", json={"name": "Dash Household"}).json()["id"]


def _division():
    return client.post("/divisions", json={"name": "Dash Division"}).json()["id"]


def _member(first="D", last="M"):
    return client.post(
        "/members",
        json={
            "first_name": first,
            "last_name": last,
            "household_id": _household(),
            "division_id": _division(),
        },
    ).json()["id"]


def _service(name="S", date="2026-07-05"):
    return client.post("/services", json={"name": name, "date": date}).json()


def test_empty_dashboard():
    dash = client.get("/dashboard").json()
    assert dash["member_count"] == 0
    assert dash["service_count"] == 0
    assert dash["attendance_count"] == 0
    assert dash["event_count"] == 0
    assert dash["campaign_count"] == 0
    assert dash["total_giving"] == 0
    assert dash["giving_by_period"] == []
    assert dash["attendance_by_service"] == []
    assert dash["campaigns"] == []


def test_dashboard_counts():
    m1 = _member()
    m2 = _member()
    svc = _service()
    client.post(f"/services/{svc['id']}/attendance", json={"member_ids": [m1, m2]})
    client.post("/events", json={"name": "E", "date": "2026-08-01"})
    client.post("/campaigns", json={"name": "C", "target_amount": 1000.0})
    client.post(
        "/donations",
        json={"amount": 100.0, "date": "2026-07-01", "donation_type": "tithe", "member_id": m1},
    )

    dash = client.get("/dashboard").json()
    assert dash["member_count"] == 2
    assert dash["service_count"] == 1
    assert dash["attendance_count"] == 2
    assert dash["event_count"] == 1
    assert dash["campaign_count"] == 1
    assert dash["total_giving"] == 100.0


def test_dashboard_attendance_by_service():
    m1 = _member()
    svc = _service("Sunday", "2026-07-12")
    client.post(f"/services/{svc['id']}/attendance", json={"member_ids": [m1]})
    dash = client.get("/dashboard").json()
    entry = next(s for s in dash["attendance_by_service"] if s["service_id"] == svc["id"])
    assert entry["present"] == 1
    assert entry["name"] == "Sunday"
    assert entry["date"] == "2026-07-12"


def test_dashboard_giving_by_period_and_campaigns():
    m1 = _member()
    c = client.post("/campaigns", json={"name": "Build", "target_amount": 500.0}).json()
    client.post(
        "/donations",
        json={"amount": 200.0, "date": "2026-07-01", "donation_type": "x", "member_id": m1, "campaign_id": c["id"]},
    )
    client.post(
        "/donations",
        json={"amount": 50.0, "date": "2026-08-01", "donation_type": "x", "member_id": m1},
    )
    dash = client.get("/dashboard").json()
    by_period = {p["period"]: p["total"] for p in dash["giving_by_period"]}
    assert by_period["2026-07"] == 200.0
    assert by_period["2026-08"] == 50.0
    camp = next(c2 for c2 in dash["campaigns"] if c2["campaign_id"] == c["id"])
    assert camp["total_raised"] == 200.0
