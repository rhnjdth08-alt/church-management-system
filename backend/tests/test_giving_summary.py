"""Tests for giving summaries (Story 3.3, AC #1-#5).

Summaries are computed read-only from the shared Donation data: grand total,
totals by month, totals by donor, plus per-campaign fundraising progress.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household():
    return client.post("/households", json={"name": "Sum Household"}).json()["id"]


def _division():
    return client.post("/divisions", json={"name": "Sum Division"}).json()["id"]


def _member(first="Don", last="Or"):
    return client.post(
        "/members",
        json={
            "first_name": first,
            "last_name": last,
            "household_id": _household(),
            "division_id": _division(),
        },
    ).json()["id"]


def _donate(amount, date, member_id=None, household_id=None, campaign_id=None):
    payload = {"amount": amount, "date": date, "donation_type": "tithe"}
    if member_id is not None:
        payload["member_id"] = member_id
    if household_id is not None:
        payload["household_id"] = household_id
    if campaign_id is not None:
        payload["campaign_id"] = campaign_id
    return client.post("/donations", json=payload)


def test_empty_summary():
    summary = client.get("/giving/summary").json()
    assert summary["grand_total"] == 0
    assert summary["by_period"] == []
    assert summary["by_donor"] == []


def test_grand_total_includes_member_and_household():
    m = _member()
    hh = _household()
    _donate(100.0, "2026-07-01", member_id=m)
    _donate(50.0, "2026-07-02", household_id=hh)
    summary = client.get("/giving/summary").json()
    assert summary["grand_total"] == 150.0


def test_by_period_groups_by_month():
    m = _member()
    _donate(100.0, "2026-07-01", member_id=m)
    _donate(40.0, "2026-07-20", member_id=m)
    _donate(60.0, "2026-08-05", member_id=m)
    summary = client.get("/giving/summary").json()
    by_period = {p["period"]: p for p in summary["by_period"]}
    assert by_period["2026-07"]["total"] == 140.0
    assert by_period["2026-07"]["count"] == 2
    assert by_period["2026-08"]["total"] == 60.0
    # Periods are in ascending order.
    periods = [p["period"] for p in summary["by_period"]]
    assert periods == sorted(periods)


def test_by_donor_groups_by_member():
    m1 = _member("Alice", "A")
    m2 = _member("Bob", "B")
    _donate(100.0, "2026-07-01", member_id=m1)
    _donate(25.0, "2026-07-02", member_id=m1)
    _donate(80.0, "2026-07-03", member_id=m2)
    summary = client.get("/giving/summary").json()
    by_donor = {d["member_id"]: d for d in summary["by_donor"]}
    assert by_donor[m1]["total"] == 125.0
    assert by_donor[m1]["count"] == 2
    assert by_donor[m2]["total"] == 80.0


def test_household_only_gift_excluded_from_by_donor_but_in_total():
    hh = _household()
    _donate(70.0, "2026-07-01", household_id=hh)
    summary = client.get("/giving/summary").json()
    assert summary["grand_total"] == 70.0
    assert summary["by_donor"] == []  # no member attribution
    assert summary["by_period"][0]["total"] == 70.0


# --- AC #3: fundraising progress alongside ---------------------------------


def test_campaigns_progress_endpoint():
    c1 = client.post(
        "/campaigns", json={"name": "C1", "target_amount": 1000.0}
    ).json()
    c2 = client.post(
        "/campaigns", json={"name": "C2", "target_amount": 500.0}
    ).json()
    m = _member()
    _donate(300.0, "2026-07-01", member_id=m, campaign_id=c1["id"])
    _donate(500.0, "2026-07-01", member_id=m, campaign_id=c2["id"])

    progress = client.get("/giving/campaigns/progress").json()
    by_id = {p["campaign_id"]: p for p in progress}
    assert by_id[c1["id"]]["total_raised"] == 300.0
    assert abs(by_id[c1["id"]]["percent_raised"] - 30.0) < 1e-6
    assert by_id[c2["id"]]["total_raised"] == 500.0
    assert by_id[c2["id"]]["remaining"] == 0.0
