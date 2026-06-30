"""Tests for directory search and filtering (Story 1.3, AC #1-#7)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _household(name="SF Household"):
    return client.post("/households", json={"name": name}).json()["id"]


def _division(name="SF Division"):
    return client.post("/divisions", json={"name": name}).json()["id"]


def _tag(name):
    return client.post("/tags", json={"name": name}).json()["id"]


def _member(first, last, household_id, division_id, status="active", tag_ids=None):
    return client.post(
        "/members",
        json={
            "first_name": first,
            "last_name": last,
            "household_id": household_id,
            "division_id": division_id,
            "status": status,
            "tag_ids": tag_ids or [],
        },
    ).json()["id"]


def _ids(params=""):
    return [m["id"] for m in client.get(f"/members{params}").json()]


# --- AC #1: name search ----------------------------------------------------


def test_search_by_first_name_partial_case_insensitive():
    h, d = _household(), _division()
    alice = _member("Alice", "Walker", h, d)
    bob = _member("Bob", "Stone", h, d)

    result = _ids("?q=ali")  # partial + lowercase
    assert alice in result
    assert bob not in result


def test_search_by_last_name():
    h, d = _household(), _division()
    target = _member("Carol", "Zimmerman", h, d)
    other = _member("Dave", "Young", h, d)

    result = _ids("?q=zimmer")
    assert target in result
    assert other not in result


def test_search_no_match_returns_empty():
    h, d = _household(), _division()
    _member("Eve", "Adams", h, d)
    assert _ids("?q=nonexistentname") == []


# --- AC #2: household filter ----------------------------------------------


def test_filter_by_household():
    h1, h2, d = _household("House One"), _household("House Two"), _division()
    in_h1 = _member("Frank", "One", h1, d)
    in_h2 = _member("Grace", "Two", h2, d)

    result = _ids(f"?household_id={h1}")
    assert in_h1 in result
    assert in_h2 not in result


# --- AC #3: status filter --------------------------------------------------


def test_filter_by_status():
    h, d = _household(), _division()
    active = _member("Hank", "Active", h, d, status="active")
    inactive = _member("Ivy", "Inactive", h, d, status="inactive")

    result = _ids("?status=inactive")
    assert inactive in result
    assert active not in result


# --- AC #4: division filter (existing behavior preserved) ------------------


def test_filter_by_division():
    h, d1, d2 = _household(), _division("Div A"), _division("Div B")
    in_d1 = _member("Jack", "A", h, d1)
    in_d2 = _member("Kate", "B", h, d2)

    result = _ids(f"?division_id={d1}")
    assert in_d1 in result
    assert in_d2 not in result


# --- AC #5: tag filter -----------------------------------------------------


def test_filter_by_tag():
    h, d = _household(), _division()
    choir = _tag("Choir Filter")
    tagged = _member("Leo", "Choir", h, d, tag_ids=[choir])
    untagged = _member("Mia", "None", h, d)

    result = _ids(f"?tag_id={choir}")
    assert tagged in result
    assert untagged not in result


# --- AC #6: combined search + filters --------------------------------------


def test_combined_search_and_filters():
    h1, h2, d = _household("Combo One"), _household("Combo Two"), _division()
    # Two "Sam"s, different households + statuses.
    match = _member("Sam", "Match", h1, d, status="active")
    wrong_house = _member("Sam", "WrongHouse", h2, d, status="active")
    wrong_status = _member("Sam", "WrongStatus", h1, d, status="inactive")
    wrong_name = _member("Tom", "Other", h1, d, status="active")

    result = _ids(f"?q=sam&household_id={h1}&status=active")
    assert match in result
    assert wrong_house not in result
    assert wrong_status not in result
    assert wrong_name not in result


def test_no_params_returns_all():
    h, d = _household(), _division()
    a = _member("All", "One", h, d)
    b = _member("All", "Two", h, d)
    result = _ids()
    assert a in result and b in result


# --- AC #7: filtering does not mutate or duplicate records ------------------


def test_filtering_does_not_mutate_records():
    h, d = _household(), _division()
    member_id = _member("Stable", "Record", h, d)

    before = client.get("/members").json()
    # Run several filtered queries.
    client.get(f"?household_id={h}")
    client.get("/members?q=stable")
    client.get("/members?status=active")
    after = client.get("/members").json()

    assert len(before) == len(after)
    assert sum(1 for m in after if m["id"] == member_id) == 1
