"""Tests for attendance recording and history (Story 2.1, AC #1-#6).

Attendance is recorded against a Service (name + date). A user marks one or
more existing members present; entries are queryable per-service and per-member.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household():
    return client.post("/households", json={"name": "Att Household"}).json()["id"]


def _division():
    return client.post("/divisions", json={"name": "Att Division"}).json()["id"]


def _member(first, last):
    return client.post(
        "/members",
        json={
            "first_name": first,
            "last_name": last,
            "household_id": _household(),
            "division_id": _division(),
        },
    ).json()["id"]


def _service(name="Sunday Service", date="2026-07-05"):
    response = client.post("/services", json={"name": name, "date": date})
    assert response.status_code == 200
    return response.json()


# --- AC #1: create / list services -----------------------------------------


def test_create_and_list_service():
    svc = _service("Easter Service", "2026-04-05")
    assert svc["name"] == "Easter Service"
    assert svc["date"] == "2026-04-05"
    assert "id" in svc

    listed = client.get("/services").json()
    assert any(s["id"] == svc["id"] for s in listed)


# --- AC #2, #3: record attendance ------------------------------------------


def test_record_attendance_for_members():
    svc = _service()
    m1 = _member("Anna", "One")
    m2 = _member("Ben", "Two")

    response = client.post(
        f"/services/{svc['id']}/attendance",
        json={"member_ids": [m1, m2]},
    )
    assert response.status_code == 200

    present = client.get(f"/services/{svc['id']}/attendance").json()
    present_ids = [m["id"] for m in present]
    assert m1 in present_ids
    assert m2 in present_ids


def test_record_attendance_is_idempotent():
    """Re-recording the same member for the same service must not duplicate."""
    svc = _service()
    m1 = _member("Carl", "Dup")

    client.post(f"/services/{svc['id']}/attendance", json={"member_ids": [m1]})
    client.post(f"/services/{svc['id']}/attendance", json={"member_ids": [m1]})

    present = client.get(f"/services/{svc['id']}/attendance").json()
    assert sum(1 for m in present if m["id"] == m1) == 1


def test_record_attendance_invalid_service():
    m1 = _member("Dana", "NoService")
    response = client.post("/services/9999/attendance", json={"member_ids": [m1]})
    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found."


def test_record_attendance_invalid_member():
    svc = _service()
    response = client.post(
        f"/services/{svc['id']}/attendance",
        json={"member_ids": [9999]},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Member not found."


# --- AC #4: per-person history ---------------------------------------------


def test_member_attendance_history():
    m1 = _member("Eve", "History")
    svc1 = _service("First Service", "2026-07-05")
    svc2 = _service("Second Service", "2026-07-12")

    client.post(f"/services/{svc1['id']}/attendance", json={"member_ids": [m1]})
    client.post(f"/services/{svc2['id']}/attendance", json={"member_ids": [m1]})

    history = client.get(f"/members/{m1}/attendance").json()
    service_ids = {h["service_id"] for h in history}
    assert {svc1["id"], svc2["id"]}.issubset(service_ids)
    # History carries the service date for each attended service (AC #3).
    dates = {h["date"] for h in history}
    assert {"2026-07-05", "2026-07-12"}.issubset(dates)


def test_member_attendance_history_empty_when_none():
    m1 = _member("Frank", "Absent")
    assert client.get(f"/members/{m1}/attendance").json() == []


# --- AC #5: per-service history --------------------------------------------


def test_service_attendance_only_lists_present_members():
    svc = _service()
    present = _member("Grace", "Present")
    absent = _member("Hank", "Absent")

    client.post(f"/services/{svc['id']}/attendance", json={"member_ids": [present]})

    listed = [m["id"] for m in client.get(f"/services/{svc['id']}/attendance").json()]
    assert present in listed
    assert absent not in listed


# --- AC #6: recording attendance does not mutate member records ------------


def test_recording_attendance_does_not_mutate_members():
    svc = _service()
    m1 = _member("Iris", "Stable")

    before = client.get("/members").json()
    client.post(f"/services/{svc['id']}/attendance", json={"member_ids": [m1]})
    after = client.get("/members").json()

    assert len(before) == len(after)
    member_after = next(m for m in after if m["id"] == m1)
    assert member_after["first_name"] == "Iris"
    assert member_after["last_name"] == "Stable"
