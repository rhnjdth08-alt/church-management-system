"""Tests for targeted announcements (Story 4.1, AC #1-#6).

An announcement is composed and "sent" to an audience resolved from the shared
member directory (reusing Story 1.3 filtering). Sending records a log entry with
the resolved recipient count; no external transport exists.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household(name="Ann Household"):
    return client.post("/households", json={"name": name}).json()["id"]


def _division(name="Ann Division"):
    return client.post("/divisions", json={"name": name}).json()["id"]


def _tag(name="Ann Tag"):
    return client.post("/tags", json={"name": name}).json()["id"]


def _member(first, last, household_id, division_id, tag_ids=None):
    return client.post(
        "/members",
        json={
            "first_name": first,
            "last_name": last,
            "household_id": household_id,
            "division_id": division_id,
            "tag_ids": tag_ids or [],
        },
    ).json()["id"]


def _send(**kwargs):
    payload = {"subject": "Hi", "body": "Body", "date": "2026-07-01"}
    payload.update(kwargs)
    return client.post("/announcements", json=payload)


# --- AC #1, #2, #4: compose + audience resolution --------------------------


def test_send_to_all_members():
    hh = _household()
    d = _division()
    _member("A", "One", hh, d)
    _member("B", "Two", hh, d)
    resp = _send()
    assert resp.status_code == 200
    assert resp.json()["recipient_count"] == 2


def test_filter_by_division():
    hh = _household()
    d1 = _division("D1")
    d2 = _division("D2")
    _member("A", "One", hh, d1)
    _member("B", "Two", hh, d1)
    _member("C", "Three", hh, d2)
    resp = _send(division_id=d1)
    assert resp.json()["recipient_count"] == 2


def test_filter_by_tag():
    hh = _household()
    d = _division()
    t = _tag("Choir")
    _member("A", "One", hh, d, tag_ids=[t])
    _member("B", "Two", hh, d)  # no tag
    resp = _send(tag_id=t)
    assert resp.json()["recipient_count"] == 1


def test_filter_by_household():
    hh1 = _household("HH1")
    hh2 = _household("HH2")
    d = _division()
    _member("A", "One", hh1, d)
    _member("B", "Two", hh2, d)
    resp = _send(household_id=hh1)
    assert resp.json()["recipient_count"] == 1


# --- AC #3: logging ---------------------------------------------------------


def test_announcement_is_logged():
    hh = _household()
    d = _division()
    _member("A", "One", hh, d)
    _send(subject="Picnic", body="Come!")
    log = client.get("/announcements").json()
    assert any(a["subject"] == "Picnic" for a in log)


def test_preview_does_not_log():
    hh = _household()
    d = _division()
    _member("A", "One", hh, d)
    before = len(client.get("/announcements").json())
    preview = client.get("/announcements/preview").json()
    assert preview["recipient_count"] == 1
    after = len(client.get("/announcements").json())
    assert before == after  # preview must not create a log entry


# --- AC #1: validation ------------------------------------------------------


def test_reject_empty_subject_or_body():
    assert _send(subject="").status_code == 400
    assert _send(body="").status_code == 400
