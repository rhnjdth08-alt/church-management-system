"""Regression tests for directory visibility and profile views (AC #3, #5)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _seed():
    household_id = client.post("/households", json={"name": "Dir Household"}).json()["id"]
    division_id = client.post("/divisions", json={"name": "Dir Division"}).json()["id"]
    return household_id, division_id


def test_created_member_appears_in_directory_immediately():
    household_id, division_id = _seed()
    created = client.post(
        "/members",
        json={
            "first_name": "Directory",
            "last_name": "Visible",
            "email": "directory.visible@example.com",
            "household_id": household_id,
            "division_id": division_id,
        },
    ).json()

    directory = client.get("/members")
    assert directory.status_code == 200
    assert created["id"] in [m["id"] for m in directory.json()]


def test_member_profile_reflects_updates():
    household_id, division_id = _seed()
    member_id = client.post(
        "/members",
        json={
            "first_name": "Profile",
            "last_name": "Original",
            "email": "profile.original@example.com",
            "household_id": household_id,
            "division_id": division_id,
        },
    ).json()["id"]

    client.put(f"/members/{member_id}", json={"last_name": "Updated", "status": "inactive"})

    profile = client.get(f"/members/{member_id}")
    assert profile.status_code == 200
    body = profile.json()
    assert body["last_name"] == "Updated"
    assert body["status"] == "inactive"


def test_update_does_not_create_duplicate_record():
    household_id, division_id = _seed()
    member_id = client.post(
        "/members",
        json={
            "first_name": "No",
            "last_name": "Duplicate",
            "email": "no.duplicate@example.com",
            "household_id": household_id,
            "division_id": division_id,
        },
    ).json()["id"]

    before = len(client.get("/members").json())
    client.put(f"/members/{member_id}", json={"phone": "555-000-1111"})
    after = client.get("/members").json()

    assert len(after) == before  # editing must not add a new record
    assert sum(1 for m in after if m["id"] == member_id) == 1
