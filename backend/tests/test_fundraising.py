"""Tests for fundraising campaigns (Story 3.2, AC #1-#5).

Campaigns track a target; pledges are commitments; contributions reuse the
Donation model (linked via campaign_id). Progress = target / pledged / raised.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household():
    return client.post("/households", json={"name": "FR Household"}).json()["id"]


def _division():
    return client.post("/divisions", json={"name": "FR Division"}).json()["id"]


def _member():
    return client.post(
        "/members",
        json={
            "first_name": "Gift",
            "last_name": "Giver",
            "household_id": _household(),
            "division_id": _division(),
        },
    ).json()["id"]


def _campaign(name="Building Fund", target=10000.0, description="New sanctuary"):
    resp = client.post(
        "/campaigns",
        json={"name": name, "target_amount": target, "description": description},
    )
    assert resp.status_code == 200
    return resp.json()


# --- AC #1: create / list campaigns ----------------------------------------


def test_create_and_list_campaign():
    c = _campaign("Roof Repair", 5000.0)
    assert c["name"] == "Roof Repair"
    assert c["target_amount"] == 5000.0
    listed = client.get("/campaigns").json()
    assert any(x["id"] == c["id"] for x in listed)


def test_reject_non_positive_target():
    assert client.post("/campaigns", json={"name": "X", "target_amount": 0}).status_code == 400
    assert client.post("/campaigns", json={"name": "X", "target_amount": -1}).status_code == 400


# --- AC #2: pledges ---------------------------------------------------------


def test_record_and_list_pledge():
    c = _campaign()
    m = _member()
    resp = client.post(
        f"/campaigns/{c['id']}/pledges", json={"amount": 500.0, "member_id": m}
    )
    assert resp.status_code == 200
    pledges = client.get(f"/campaigns/{c['id']}/pledges").json()
    assert len(pledges) == 1
    assert pledges[0]["amount"] == 500.0


def test_pledge_invalid_campaign_404():
    resp = client.post("/campaigns/9999/pledges", json={"amount": 100.0})
    assert resp.status_code == 404


def test_pledge_non_positive_amount_400():
    c = _campaign()
    assert client.post(f"/campaigns/{c['id']}/pledges", json={"amount": 0}).status_code == 400


# --- AC #3: contributions reuse Donation -----------------------------------


def test_contribution_via_donation_with_campaign_id():
    c = _campaign()
    m = _member()
    resp = client.post(
        "/donations",
        json={
            "amount": 250.0,
            "date": "2026-07-01",
            "donation_type": "building",
            "member_id": m,
            "campaign_id": c["id"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["campaign_id"] == c["id"]


def test_donation_unknown_campaign_404():
    """An unknown campaign on a donation is 404 — consistent with the pledge
    endpoint, which 404s the same missing-campaign condition."""
    m = _member()
    resp = client.post(
        "/donations",
        json={
            "amount": 100.0,
            "date": "2026-07-01",
            "donation_type": "building",
            "member_id": m,
            "campaign_id": 9999,
        },
    )
    assert resp.status_code == 404


# --- AC #4: progress --------------------------------------------------------


def test_campaign_progress_math():
    c = _campaign("Goal", 1000.0)
    m = _member()
    # Two pledges totaling 600, two contributions totaling 400.
    client.post(f"/campaigns/{c['id']}/pledges", json={"amount": 400.0, "member_id": m})
    client.post(f"/campaigns/{c['id']}/pledges", json={"amount": 200.0})
    for amt in (300.0, 100.0):
        client.post(
            "/donations",
            json={
                "amount": amt,
                "date": "2026-07-01",
                "donation_type": "building",
                "member_id": m,
                "campaign_id": c["id"],
            },
        )

    prog = client.get(f"/campaigns/{c['id']}/progress").json()
    assert prog["target"] == 1000.0
    assert prog["total_pledged"] == 600.0
    assert prog["total_raised"] == 400.0
    assert prog["remaining"] == 600.0  # target - raised
    assert abs(prog["percent_raised"] - 40.0) < 1e-6


def test_campaign_progress_invalid_404():
    assert client.get("/campaigns/9999/progress").status_code == 404


def test_progress_zero_target_does_not_crash():
    """A campaign row with target_amount == 0 (only reachable via direct DB
    writes, since create_campaign rejects it) must not 500 the progress
    endpoints — percent is reported as 0 instead of dividing by zero."""
    from sqlmodel import Session

    from app.database import engine
    from app.models import FundraisingCampaign

    with Session(engine) as session:
        c = FundraisingCampaign(name="Legacy", target_amount=0.0)
        session.add(c)
        session.commit()
        session.refresh(c)
        cid = c.id

    resp = client.get(f"/campaigns/{cid}/progress")
    assert resp.status_code == 200
    assert resp.json()["percent_raised"] == 0.0
    # The all-campaigns fan-out and CSV export must also survive the 0-target row.
    assert client.get("/giving/campaigns/progress").status_code == 200
    assert client.get("/exports/fundraising.csv").status_code == 200


def test_progress_remaining_not_negative_when_overfunded():
    c = _campaign("Small", 100.0)
    m = _member()
    client.post(
        "/donations",
        json={
            "amount": 250.0,
            "date": "2026-07-01",
            "donation_type": "building",
            "member_id": m,
            "campaign_id": c["id"],
        },
    )
    prog = client.get(f"/campaigns/{c['id']}/progress").json()
    assert prog["total_raised"] == 250.0
    assert prog["remaining"] == 0.0  # clamped, not negative
