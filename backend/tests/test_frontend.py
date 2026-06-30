from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_serves_member_app():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text.lower()
    # The dedicated form and directory must be present in the UI (AC #1, #5).
    assert "member" in body
    assert "<form" in body


def test_member_form_supports_multiple_divisions():
    """The UI must let an administrator pick one or more divisions (AC #1)."""
    body = client.get("/").text
    # A multi-select control bound to the new division_ids list assignment.
    assert 'id="division_ids"' in body
    assert "multiple" in body.lower()


def test_directory_has_search_and_filter_controls():
    """The directory must expose search + filter controls (Story 1.3)."""
    body = client.get("/").text
    assert 'id="search-q"' in body  # name search input
    assert 'id="filter-household"' in body
    assert 'id="filter-status"' in body
    assert 'id="filter-division"' in body
    assert 'id="filter-tag"' in body
    assert 'id="clear-filters"' in body


def test_member_form_supports_tags():
    """The member form must allow assigning ministry tags (Story 1.3)."""
    body = client.get("/").text
    assert 'id="tag_ids"' in body


def test_attendance_ui_controls_present():
    """The UI must let a leader create a service and record attendance (Story 2.1)."""
    body = client.get("/").text
    assert 'id="service-name"' in body  # new-service name input
    assert 'id="service-date"' in body  # new-service date input
    assert 'id="attendance-panel"' in body  # the attendance recording panel


def test_attendance_by_division_breakdown_present():
    """The UI must show a per-division attendance breakdown (Story 2.2)."""
    body = client.get("/").text
    assert 'id="attendance-by-division"' in body


def test_events_ui_controls_present():
    """The UI must let a coordinator create an event and RSVP members (Story 2.3)."""
    body = client.get("/").text
    assert 'id="events-panel"' in body
    assert 'id="event-name"' in body
    assert 'id="event-date"' in body


def test_giving_ui_controls_present():
    """The UI must let an admin record donations (Story 3.1)."""
    body = client.get("/").text
    assert 'id="giving-panel"' in body
    assert 'id="donation-amount"' in body
    assert 'id="donation-date"' in body
