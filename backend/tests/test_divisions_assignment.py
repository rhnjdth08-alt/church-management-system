"""Tests for Story 1.2 — assign members to one or more divisions.

Covers:
- AC #1: member create/edit supports selecting one or more divisions.
- AC #2: default division categories include Sunday School, Youth, Adult class.
- AC #3: assigned divisions are visible on the profile and directory listings.
- AC #4: division assignments are persisted and queryable for filtering.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household():
    return client.post("/households", json={"name": "Assign Household"}).json()["id"]


def _division(name):
    return client.post("/divisions", json={"name": name}).json()["id"]


# --- AC #2: default division categories are seeded -------------------------


def test_default_divisions_are_seeded():
    names = {d["name"] for d in client.get("/divisions").json()}
    assert {"Sunday School", "Youth", "Adult Class"}.issubset(names)


# --- AC #1 + #4: assign one or more divisions on create --------------------


def test_create_member_with_multiple_divisions():
    household_id = _household()
    a = _division("Choir")
    b = _division("Ushers")

    response = client.post(
        "/members",
        json={
            "first_name": "Multi",
            "last_name": "Division",
            "household_id": household_id,
            "division_id": a,
            "division_ids": [a, b],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data["division_ids"]) == {a, b}
    # Primary division remains exposed for backward compatibility.
    assert data["division_id"] == a


def test_create_member_division_id_seeds_division_ids_when_omitted():
    """A member created with only the legacy single division_id is still
    reported as belonging to that division in the new list field."""
    household_id = _household()
    a = _division("Single")

    response = client.post(
        "/members",
        json={
            "first_name": "Legacy",
            "last_name": "Single",
            "household_id": household_id,
            "division_id": a,
        },
    )
    assert response.status_code == 200
    assert response.json()["division_ids"] == [a]


def test_create_member_with_invalid_division_in_list_fails():
    household_id = _household()
    a = _division("Valid")

    response = client.post(
        "/members",
        json={
            "first_name": "Bad",
            "last_name": "List",
            "household_id": household_id,
            "division_id": a,
            "division_ids": [a, 9999],
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Division not found."


# --- AC #1 + #4: edit a member's divisions ---------------------------------


def test_update_member_divisions():
    household_id = _household()
    a = _division("First")
    b = _division("Second")
    c = _division("Third")

    member_id = client.post(
        "/members",
        json={
            "first_name": "Edit",
            "last_name": "Divisions",
            "household_id": household_id,
            "division_id": a,
            "division_ids": [a],
        },
    ).json()["id"]

    response = client.put(
        f"/members/{member_id}",
        json={"division_ids": [b, c]},
    )
    assert response.status_code == 200
    assert set(response.json()["division_ids"]) == {b, c}


def test_update_member_divisions_rejects_invalid():
    household_id = _household()
    a = _division("OnlyValid")
    member_id = client.post(
        "/members",
        json={
            "first_name": "Edit",
            "last_name": "BadDivisions",
            "household_id": household_id,
            "division_id": a,
            "division_ids": [a],
        },
    ).json()["id"]

    response = client.put(
        f"/members/{member_id}",
        json={"division_ids": [a, 8888]},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Division not found."


# --- AC #3: divisions visible in directory + profile -----------------------


def test_directory_and_profile_expose_division_ids():
    household_id = _household()
    a = _division("Visible A")
    b = _division("Visible B")

    member_id = client.post(
        "/members",
        json={
            "first_name": "Shown",
            "last_name": "Member",
            "household_id": household_id,
            "division_id": a,
            "division_ids": [a, b],
        },
    ).json()["id"]

    listed = next(m for m in client.get("/members").json() if m["id"] == member_id)
    assert set(listed["division_ids"]) == {a, b}

    profile = client.get(f"/members/{member_id}").json()
    assert set(profile["division_ids"]) == {a, b}


# --- AC #4: filter the directory by division -------------------------------


def test_filter_members_by_division():
    household_id = _household()
    a = _division("Filter A")
    b = _division("Filter B")

    in_a = client.post(
        "/members",
        json={
            "first_name": "In",
            "last_name": "A",
            "household_id": household_id,
            "division_id": a,
            "division_ids": [a],
        },
    ).json()["id"]
    in_b = client.post(
        "/members",
        json={
            "first_name": "In",
            "last_name": "B",
            "household_id": household_id,
            "division_id": b,
            "division_ids": [b],
        },
    ).json()["id"]

    filtered = client.get(f"/members?division_id={a}").json()
    ids = [m["id"] for m in filtered]
    assert in_a in ids
    assert in_b not in ids
