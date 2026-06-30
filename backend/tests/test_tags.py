"""Tests for ministry tags (Story 1.3, AC #5).

Tags are reusable first-class entities (like divisions): a Tag table plus a
MemberTagLink many-to-many association. Tags are optional on a member.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household():
    return client.post("/households", json={"name": "Tag Household"}).json()["id"]


def _division():
    return client.post("/divisions", json={"name": "Tag Division"}).json()["id"]


def _tag(name):
    response = client.post("/tags", json={"name": name})
    assert response.status_code == 200
    return response.json()["id"]


def test_create_and_list_tags():
    tid = _tag("Choir")
    names = [t["name"] for t in client.get("/tags").json()]
    assert "Choir" in names
    assert any(t["id"] == tid for t in client.get("/tags").json())


def test_create_member_with_tags():
    household_id = _household()
    division_id = _division()
    a = _tag("Greeter")
    b = _tag("Usher")

    response = client.post(
        "/members",
        json={
            "first_name": "Tagged",
            "last_name": "Member",
            "household_id": household_id,
            "division_id": division_id,
            "tag_ids": [a, b],
        },
    )
    assert response.status_code == 200
    assert set(response.json()["tag_ids"]) == {a, b}


def test_member_without_tags_defaults_empty():
    household_id = _household()
    division_id = _division()
    response = client.post(
        "/members",
        json={
            "first_name": "Untagged",
            "last_name": "Member",
            "household_id": household_id,
            "division_id": division_id,
        },
    )
    assert response.status_code == 200
    assert response.json()["tag_ids"] == []


def test_create_member_with_invalid_tag_fails():
    household_id = _household()
    division_id = _division()
    response = client.post(
        "/members",
        json={
            "first_name": "Bad",
            "last_name": "Tag",
            "household_id": household_id,
            "division_id": division_id,
            "tag_ids": [9999],
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Tag not found."


def test_update_member_tags():
    household_id = _household()
    division_id = _division()
    a = _tag("Old Tag")
    b = _tag("New Tag")
    c = _tag("Another Tag")

    member_id = client.post(
        "/members",
        json={
            "first_name": "Edit",
            "last_name": "Tags",
            "household_id": household_id,
            "division_id": division_id,
            "tag_ids": [a],
        },
    ).json()["id"]

    response = client.put(f"/members/{member_id}", json={"tag_ids": [b, c]})
    assert response.status_code == 200
    assert set(response.json()["tag_ids"]) == {b, c}


def test_update_member_tags_can_clear():
    household_id = _household()
    division_id = _division()
    a = _tag("Clearable")
    member_id = client.post(
        "/members",
        json={
            "first_name": "Clear",
            "last_name": "Tags",
            "household_id": household_id,
            "division_id": division_id,
            "tag_ids": [a],
        },
    ).json()["id"]

    response = client.put(f"/members/{member_id}", json={"tag_ids": []})
    assert response.status_code == 200
    assert response.json()["tag_ids"] == []
