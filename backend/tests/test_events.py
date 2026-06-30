"""Tests for events and RSVPs (Story 2.3, AC #1-#6).

Events are a distinct domain from Services/Attendance. An RSVP records whether a
member will attend ("yes"/"no"); it is idempotent per member+event and counts
toward the event's attendee total.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household():
    return client.post("/households", json={"name": "Event Household"}).json()["id"]


def _division():
    return client.post("/divisions", json={"name": "Event Division"}).json()["id"]


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


def _event(name="Picnic", date="2026-08-01", location="Park", description="Fun"):
    resp = client.post(
        "/events",
        json={"name": name, "date": date, "location": location, "description": description},
    )
    assert resp.status_code == 200
    return resp.json()


# --- AC #1: create / list events -------------------------------------------


def test_create_and_list_event():
    ev = _event("Retreat", "2026-09-10", "Lodge", "Weekend retreat")
    assert ev["name"] == "Retreat"
    assert ev["date"] == "2026-09-10"
    assert ev["location"] == "Lodge"
    assert ev["description"] == "Weekend retreat"
    assert "id" in ev

    listed = client.get("/events").json()
    assert any(e["id"] == ev["id"] for e in listed)


def test_create_event_minimal_fields():
    resp = client.post("/events", json={"name": "Minimal", "date": "2026-08-15"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["location"] is None
    assert body["description"] is None


# --- AC #2, #3: RSVP and idempotency ---------------------------------------


def test_rsvp_yes_and_no():
    ev = _event()
    m1 = _member("Rsvp", "Yes")
    m2 = _member("Rsvp", "No")

    client.post(f"/events/{ev['id']}/rsvps", json={"member_id": m1, "response": "yes"})
    client.post(f"/events/{ev['id']}/rsvps", json={"member_id": m2, "response": "no"})

    rsvps = client.get(f"/events/{ev['id']}/rsvps").json()
    by_member = {r["member_id"]: r["response"] for r in rsvps}
    assert by_member[m1] == "yes"
    assert by_member[m2] == "no"


def test_rsvp_is_idempotent_and_updates_response():
    ev = _event()
    m1 = _member("Change", "Mind")

    client.post(f"/events/{ev['id']}/rsvps", json={"member_id": m1, "response": "yes"})
    summary = client.post(
        f"/events/{ev['id']}/rsvps", json={"member_id": m1, "response": "no"}
    ).json()

    rsvps = client.get(f"/events/{ev['id']}/rsvps").json()
    assert sum(1 for r in rsvps if r["member_id"] == m1) == 1  # no duplicate
    assert next(r for r in rsvps if r["member_id"] == m1)["response"] == "no"
    assert summary["yes_count"] == 0
    assert summary["no_count"] == 1


def test_rsvp_invalid_event_returns_404():
    m1 = _member("No", "Event")
    resp = client.post("/events/9999/rsvps", json={"member_id": m1, "response": "yes"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Event not found."


def test_rsvp_invalid_member_returns_400():
    ev = _event()
    resp = client.post(
        f"/events/{ev['id']}/rsvps", json={"member_id": 9999, "response": "yes"}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Member not found."


def test_rsvp_invalid_response_returns_400():
    ev = _event()
    m1 = _member("Bad", "Response")
    resp = client.post(
        f"/events/{ev['id']}/rsvps", json={"member_id": m1, "response": "maybe"}
    )
    assert resp.status_code == 400


# --- AC #4: attendee count / summary ---------------------------------------


def test_event_summary_counts():
    ev = _event()
    yes_members = [_member("Y", str(i)) for i in range(3)]
    no_members = [_member("N", str(i)) for i in range(2)]
    for m in yes_members:
        client.post(f"/events/{ev['id']}/rsvps", json={"member_id": m, "response": "yes"})
    for m in no_members:
        client.post(f"/events/{ev['id']}/rsvps", json={"member_id": m, "response": "no"})

    summary = client.get(f"/events/{ev['id']}/summary").json()
    assert summary["yes_count"] == 3
    assert summary["no_count"] == 2
    assert summary["total"] == 5


def test_event_summary_invalid_event_returns_404():
    assert client.get("/events/9999/summary").status_code == 404
    assert client.get("/events/9999/rsvps").status_code == 404


# --- AC #6: RSVP does not mutate member records ----------------------------


def test_rsvp_does_not_mutate_members():
    ev = _event()
    m1 = _member("Stable", "Member")

    before = client.get("/members").json()
    client.post(f"/events/{ev['id']}/rsvps", json={"member_id": m1, "response": "yes"})
    after = client.get("/members").json()

    assert len(before) == len(after)
    member_after = next(m for m in after if m["id"] == m1)
    assert member_after["first_name"] == "Stable"
