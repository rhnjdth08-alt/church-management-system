"""Tests for division attendance tracking (Story 2.2, AC #1-#6).

Division attendance is derived from the existing Story 2.1 data model
(``AttendanceRecord`` + ``MemberDivisionLink``) — no new attendance store. A
present member counts toward every division they belong to.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household():
    return client.post("/households", json={"name": "Div Att Household"}).json()["id"]


def _division(name):
    return client.post("/divisions", json={"name": name}).json()["id"]


def _member(first, last, division_id, extra_division_ids=None):
    """Create a member assigned to ``division_id`` (primary) plus any extras."""
    division_ids = [division_id] + list(extra_division_ids or [])
    return client.post(
        "/members",
        json={
            "first_name": first,
            "last_name": last,
            "household_id": _household(),
            "division_id": division_id,
            "division_ids": division_ids,
        },
    ).json()["id"]


def _service(name="Sunday Service", date="2026-07-05"):
    return client.post("/services", json={"name": name, "date": date}).json()


def _record(service_id, member_ids):
    return client.post(
        f"/services/{service_id}/attendance", json={"member_ids": member_ids}
    )


# --- AC #1: per-service breakdown by division ------------------------------


def test_by_division_counts_present_members_per_division():
    sunday = _division("Sunday School A")
    youth = _division("Youth A")
    svc = _service()
    s1 = _member("Sam", "Sunday", sunday)
    s2 = _member("Sara", "Sunday", sunday)
    y1 = _member("Yan", "Youth", youth)
    _record(svc["id"], [s1, s2, y1])

    resp = client.get(f"/services/{svc['id']}/attendance/by-division")
    assert resp.status_code == 200
    counts = {row["division_id"]: row for row in resp.json()}
    assert counts[sunday]["present"] == 2
    assert counts[sunday]["division_name"] == "Sunday School A"
    assert counts[youth]["present"] == 1


def test_by_division_member_in_two_divisions_counts_in_both():
    sunday = _division("Sunday School B")
    youth = _division("Youth B")
    svc = _service()
    # One member belongs to BOTH divisions and should count in each.
    both = _member("Bo", "Both", sunday, extra_division_ids=[youth])
    _record(svc["id"], [both])

    counts = {
        row["division_id"]: row["present"]
        for row in client.get(f"/services/{svc['id']}/attendance/by-division").json()
    }
    assert counts.get(sunday) == 1
    assert counts.get(youth) == 1


def test_by_division_excludes_divisions_with_no_present_members():
    sunday = _division("Sunday School C")
    empty = _division("Empty Division C")
    svc = _service()
    s1 = _member("Solo", "Sunday", sunday)
    _record(svc["id"], [s1])

    division_ids = {
        row["division_id"]
        for row in client.get(f"/services/{svc['id']}/attendance/by-division").json()
    }
    assert sunday in division_ids
    assert empty not in division_ids


def test_by_division_invalid_service_returns_404():
    resp = client.get("/services/9999/attendance/by-division")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Service not found."


# --- AC #2: per-division summary by date/class -----------------------------


def test_division_attendance_summary_per_service():
    sunday = _division("Sunday School D")
    s1 = _member("Dee", "One", sunday)
    s2 = _member("Dee", "Two", sunday)
    svc1 = _service("First", "2026-07-05")
    svc2 = _service("Second", "2026-07-12")
    _record(svc1["id"], [s1, s2])
    _record(svc2["id"], [s1])

    summary = client.get(f"/divisions/{sunday}/attendance").json()
    by_service = {row["service_id"]: row for row in summary}
    assert by_service[svc1["id"]]["present"] == 2
    assert by_service[svc1["id"]]["date"] == "2026-07-05"
    assert by_service[svc1["id"]]["name"] == "First"
    assert by_service[svc2["id"]]["present"] == 1
    assert by_service[svc2["id"]]["date"] == "2026-07-12"


def test_division_attendance_summary_empty_when_no_attendance():
    division = _division("Quiet Division E")
    assert client.get(f"/divisions/{division}/attendance").json() == []


def test_division_attendance_summary_invalid_division_returns_404():
    resp = client.get("/divisions/9999/attendance")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Division not found."


# --- AC #3: compare participation across divisions -------------------------


def test_compare_participation_across_divisions():
    sunday = _division("Sunday School F")
    youth = _division("Youth F")
    svc = _service()
    sundays = [_member("S", str(i), sunday) for i in range(3)]
    youths = [_member("Y", str(i), youth) for i in range(1)]
    _record(svc["id"], sundays + youths)

    counts = {
        row["division_name"]: row["present"]
        for row in client.get(f"/services/{svc['id']}/attendance/by-division").json()
    }
    assert counts["Sunday School F"] == 3
    assert counts["Youth F"] == 1
    # Sunday School clearly out-participates Youth at this service.
    assert counts["Sunday School F"] > counts["Youth F"]


# --- Regression: primary-division change stays visible to by-division ------


def test_changing_primary_division_keeps_member_visible_in_by_division():
    """Updating only division_id (no division_ids) must keep the link table in
    sync, so the member is still counted under their new division."""
    old_div = _division("Old Div H")
    new_div = _division("New Div H")
    svc = _service()
    m1 = _member("Move", "Me", old_div)
    _record(svc["id"], [m1])

    # Move the member's primary division WITHOUT sending division_ids.
    resp = client.put(f"/members/{m1}", json={"division_id": new_div})
    assert resp.status_code == 200
    assert new_div in resp.json()["division_ids"]

    counts = {
        row["division_id"]: row["present"]
        for row in client.get(f"/services/{svc['id']}/attendance/by-division").json()
    }
    # The member now counts under the new division, not stranded under the old.
    assert counts.get(new_div) == 1
    # And the per-division summary for the new division reflects the attendance.
    summary = client.get(f"/divisions/{new_div}/attendance").json()
    assert any(row["service_id"] == svc["id"] for row in summary)


# --- AC #5: regression — members and 2.1 endpoints unchanged ---------------


def test_division_attendance_does_not_mutate_members():
    sunday = _division("Sunday School G")
    svc = _service()
    m1 = _member("Stable", "Member", sunday)

    before = client.get("/members").json()
    _record(svc["id"], [m1])
    client.get(f"/services/{svc['id']}/attendance/by-division")
    client.get(f"/divisions/{sunday}/attendance")
    after = client.get("/members").json()

    assert len(before) == len(after)
    member_after = next(m for m in after if m["id"] == m1)
    assert member_after["first_name"] == "Stable"
    # Story 2.1 per-service attendance still returns the present member.
    present = [m["id"] for m in client.get(f"/services/{svc['id']}/attendance").json()]
    assert m1 in present
