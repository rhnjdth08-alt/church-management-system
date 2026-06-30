from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_household_and_division_then_member():
    household_response = client.post(
        "/households",
        json={"name": "Doe Family", "address": "123 Church St"},
    )
    assert household_response.status_code == 200
    household_id = household_response.json()["id"]

    division_response = client.post(
        "/divisions",
        json={"name": "Sunday School", "description": "Children class"},
    )
    assert division_response.status_code == 200
    division_id = division_response.json()["id"]

    member_response = client.post(
        "/members",
        json={
            "first_name": "Anna",
            "last_name": "Taylor",
            "email": "anna.taylor@example.com",
            "phone": "555-7777",
            "status": "active",
            "household_id": household_id,
            "division_id": division_id,
        },
    )
    assert member_response.status_code == 200
    member = member_response.json()
    assert member["household_id"] == household_id
    assert member["division_id"] == division_id


def test_update_member_division():
    household_response = client.post(
        "/households",
        json={"name": "Smith Family", "address": "456 Ministry Rd"},
    )
    household_id = household_response.json()["id"]

    division_response = client.post(
        "/divisions",
        json={"name": "Youth", "description": "Teen ministry"},
    )
    division_id = division_response.json()["id"]

    member_response = client.post(
        "/members",
        json={
            "first_name": "Mark",
            "last_name": "Johnson",
            "email": "mark.johnson@example.com",
            "status": "active",
            "household_id": household_id,
            "division_id": division_id,
        },
    )
    member_id = member_response.json()["id"]

    new_division_response = client.post(
        "/divisions",
        json={"name": "Adult Class", "description": "Adult ministry"},
    )
    new_division_id = new_division_response.json()["id"]

    update_response = client.put(
        f"/members/{member_id}",
        json={"division_id": new_division_id},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["division_id"] == new_division_id


def test_member_with_invalid_household_fails():
    # create a valid division so only household is invalid
    division_response = client.post(
        "/divisions",
        json={"name": "Test Division", "description": "Temp"},
    )
    division_id = division_response.json()["id"]

    response = client.post(
        "/members",
        json={
            "first_name": "Invalid",
            "last_name": "Household",
            "household_id": 9999,
            "division_id": division_id,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Household not found."


def test_member_with_invalid_division_fails():
    # create a valid household so only division is invalid
    household_response = client.post(
        "/households",
        json={"name": "Temp Household"},
    )
    household_id = household_response.json()["id"]

    response = client.post(
        "/members",
        json={
            "first_name": "Invalid",
            "last_name": "Division",
            "household_id": household_id,
            "division_id": 9999,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Division not found."
