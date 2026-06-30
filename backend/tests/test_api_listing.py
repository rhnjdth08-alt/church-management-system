from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_households_includes_created():
    created = client.post(
        "/households",
        json={"name": "Listing Household", "address": "1 List Way"},
    ).json()

    response = client.get("/households")
    assert response.status_code == 200
    ids = [h["id"] for h in response.json()]
    assert created["id"] in ids


def test_list_divisions_includes_created():
    created = client.post(
        "/divisions",
        json={"name": "Listing Division", "description": "For listing"},
    ).json()

    response = client.get("/divisions")
    assert response.status_code == 200
    ids = [d["id"] for d in response.json()]
    assert created["id"] in ids
