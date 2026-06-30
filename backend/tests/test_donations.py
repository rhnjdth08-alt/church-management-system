"""Tests for recording donations (Story 3.1, AC #1-#5).

Donations reference shared Member/Household records and are queryable as giving
history per member and per household.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household(name="Giving Household"):
    return client.post("/households", json={"name": name}).json()["id"]


def _division():
    return client.post("/divisions", json={"name": "Giving Division"}).json()["id"]


def _member(first="Gen", last="Erous", household_id=None):
    return client.post(
        "/members",
        json={
            "first_name": first,
            "last_name": last,
            "household_id": household_id or _household(),
            "division_id": _division(),
        },
    ).json()["id"]


def _donate(**kwargs):
    payload = {"amount": 100.0, "date": "2026-07-01", "donation_type": "tithe"}
    payload.update(kwargs)
    return client.post("/donations", json=payload)


# --- AC #1, #2: record donations -------------------------------------------


def test_record_donation_for_member():
    m = _member()
    resp = _donate(member_id=m, amount=50.0, donation_type="offering")
    assert resp.status_code == 200
    body = resp.json()
    assert body["amount"] == 50.0
    assert body["donation_type"] == "offering"
    assert body["member_id"] == m


def test_record_donation_for_household():
    hh = _household()
    resp = _donate(household_id=hh, amount=250.0)
    assert resp.status_code == 200
    assert resp.json()["household_id"] == hh


# --- AC #3: view history ----------------------------------------------------


def test_list_and_member_history():
    m = _member()
    _donate(member_id=m, amount=10.0)
    _donate(member_id=m, amount=20.0)

    all_donations = client.get("/donations").json()
    assert len([d for d in all_donations if d["member_id"] == m]) == 2

    history = client.get(f"/members/{m}/donations").json()
    amounts = sorted(d["amount"] for d in history)
    assert amounts == [10.0, 20.0]


def test_household_history():
    hh = _household()
    _donate(household_id=hh, amount=75.0)
    history = client.get(f"/households/{hh}/donations").json()
    assert len(history) == 1
    assert history[0]["amount"] == 75.0


def test_member_history_invalid_member_404():
    assert client.get("/members/9999/donations").status_code == 404


def test_household_history_invalid_household_404():
    assert client.get("/households/9999/donations").status_code == 404


# --- AC #4: validation ------------------------------------------------------


def test_reject_non_positive_amount():
    m = _member()
    assert _donate(member_id=m, amount=0).status_code == 400
    assert _donate(member_id=m, amount=-5).status_code == 400


def test_reject_missing_donor():
    resp = _donate(amount=10.0)  # no member_id or household_id
    assert resp.status_code == 400


def test_reject_invalid_member():
    assert _donate(member_id=9999).status_code == 400


def test_reject_invalid_household():
    assert _donate(household_id=9999).status_code == 400


# --- AC #5: donations don't mutate members ---------------------------------


def test_donation_does_not_mutate_members():
    m = _member("Stable", "Donor")
    before = client.get("/members").json()
    _donate(member_id=m, amount=99.0)
    after = client.get("/members").json()
    assert len(before) == len(after)
    member_after = next(x for x in after if x["id"] == m)
    assert member_after["first_name"] == "Stable"
