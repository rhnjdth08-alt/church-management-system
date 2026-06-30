from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_household(client):
    response = client.post(
        "/households",
        json={"name": "Doe Family", "address": "123 Church St"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def create_division(client, name="Sunday School"):
    response = client.post(
        "/divisions",
        json={"name": name, "description": f"{name} class"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_create_member():
    household_id = create_household(client)
    division_id = create_division(client, "Sunday School")

    response = client.post(
        "/members",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "555-1234",
            "status": "active",
            "household_id": household_id,
            "division_id": division_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["email"] == "john.doe@example.com"
    assert data["household_id"] == household_id
    assert data["division_id"] == division_id
    assert "id" in data


def test_update_member():
    household_id = create_household(client)
    division_id = create_division(client, "Youth")
    member_response = client.post(
        "/members",
        json={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "555-5678",
            "status": "active",
            "household_id": household_id,
            "division_id": division_id,
        },
    )
    assert member_response.status_code == 200
    member_id = member_response.json()["id"]

    new_division_id = create_division(client, "Adult Class")

    update_response = client.put(
        f"/members/{member_id}",
        json={
            "phone": "555-9999",
            "division_id": new_division_id,
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["phone"] == "555-9999"
    assert updated["division_id"] == new_division_id


def test_invalid_email_rejected():
    household_id = create_household(client)
    division_id = create_division(client, "Adult Class")

    response = client.post(
        "/members",
        json={
            "first_name": "Invalid",
            "last_name": "Email",
            "email": "invalid-email",
            "household_id": household_id,
            "division_id": division_id,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email format."
