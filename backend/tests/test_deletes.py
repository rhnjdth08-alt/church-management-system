"""Delete endpoints for members, households, and tags.

Deletes must be safe: removing a household or tag detaches it from members
(and from giving/announcement records) but never deletes the member or the
financial history.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household(name="Doe Family"):
    r = client.post("/households", json={"name": name})
    assert r.status_code == 200
    return r.json()["id"]


def _division(name="Sunday School"):
    r = client.post("/divisions", json={"name": name})
    assert r.status_code == 200
    return r.json()["id"]


def _tag(name="Choir"):
    r = client.post("/tags", json={"name": name})
    assert r.status_code == 200
    return r.json()["id"]


def _member(household_id, division_id, tag_ids=None):
    r = client.post(
        "/members",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "status": "active",
            "household_id": household_id,
            "division_id": division_id,
            "division_ids": [division_id],
            "tag_ids": tag_ids or [],
        },
    )
    assert r.status_code == 200
    return r.json()["id"]


def test_delete_member_removes_it():
    member_id = _member(_household(), _division(), [_tag()])
    r = client.delete(f"/members/{member_id}")
    assert r.status_code == 204
    assert client.get(f"/members/{member_id}").status_code == 404


def test_delete_missing_member_returns_404():
    assert client.delete("/members/9999").status_code == 404


def test_delete_member_keeps_donation_but_detaches():
    household_id = _household()
    member_id = _member(household_id, _division())
    # Record the gift against both the member and the household so we can still
    # find it (via the household) after the member is gone.
    don = client.post(
        "/donations",
        json={
            "amount": 50.0,
            "date": "2026-01-01",
            "donation_type": "tithe",
            "member_id": member_id,
            "household_id": household_id,
        },
    )
    assert don.status_code == 200

    assert client.delete(f"/members/{member_id}").status_code == 204

    # The donation survives the member deletion, detached from the member.
    donations = client.get(f"/households/{household_id}/donations").json()
    assert any(d["amount"] == 50.0 and d["member_id"] is None for d in donations)


def test_delete_household_detaches_members():
    household_id = _household()
    member_id = _member(household_id, _division())

    assert client.delete(f"/households/{household_id}").status_code == 204

    # Household is gone, but the member remains (with no household).
    assert all(h["id"] != household_id for h in client.get("/households").json())
    member = client.get(f"/members/{member_id}").json()
    assert member["household_id"] is None


def test_delete_missing_household_returns_404():
    assert client.delete("/households/9999").status_code == 404


def test_delete_tag_removes_it_from_member():
    tag_id = _tag()
    member_id = _member(_household(), _division(), [tag_id])

    assert client.delete(f"/tags/{tag_id}").status_code == 204

    assert all(t["id"] != tag_id for t in client.get("/tags").json())
    member = client.get(f"/members/{member_id}").json()
    assert tag_id not in member["tag_ids"]


def test_delete_missing_tag_returns_404():
    assert client.delete("/tags/9999").status_code == 404
