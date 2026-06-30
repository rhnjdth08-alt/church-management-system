import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, func, select

from .database import create_db_and_tables, engine, get_session
from .models import (
    AttendanceRecord,
    Division,
    Donation,
    Event,
    EventRSVP,
    Household,
    Member,
    MemberDivisionLink,
    MemberTagLink,
    Service,
    Tag,
)
from .schemas import (
    AttendanceCreate,
    AttendanceHistoryEntry,
    DivisionAttendanceCount,
    DivisionAttendanceSummaryEntry,
    DivisionCreate,
    DonationCreate,
    DonationRead,
    EventCreate,
    EventRead,
    EventRSVPSummary,
    HouseholdCreate,
    MemberCreate,
    MemberRead,
    MemberUpdate,
    RSVPCreate,
    RSVPRead,
    ServiceCreate,
    ServiceRead,
    TagCreate,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

# Default division categories required by Story 1.2 (AC #2).
DEFAULT_DIVISIONS = ["Sunday School", "Youth", "Adult Class"]

# Allow digits and common phone punctuation, requiring at least 7 digits.
_PHONE_PATTERN = re.compile(r"^[0-9+\-\s().]+$")


def _is_valid_phone(phone: str) -> bool:
    if not _PHONE_PATTERN.match(phone):
        return False
    return sum(char.isdigit() for char in phone) >= 7


def seed_default_divisions() -> None:
    """Ensure the baseline division categories exist (AC #2).

    Idempotent: only inserts categories that are not already present, so it is
    safe to run on every startup.
    """
    with Session(engine) as session:
        existing = {d.name for d in session.exec(select(Division)).all()}
        for name in DEFAULT_DIVISIONS:
            if name not in existing:
                session.add(Division(name=name))
        session.commit()


def _to_read(member: Member) -> MemberRead:
    """Serialize a Member into the API response, including division/tag ids."""
    division_ids = [d.id for d in member.divisions if d.id is not None]
    tag_ids = [t.id for t in member.tags if t.id is not None]
    return MemberRead(
        id=member.id,
        first_name=member.first_name,
        last_name=member.last_name,
        email=member.email,
        phone=member.phone,
        status=member.status,
        household_id=member.household_id,
        division_id=member.division_id,
        division_ids=division_ids,
        tag_ids=tag_ids,
    )


def _resolve_tag_ids(session: Session, tag_ids: Optional[List[int]]) -> List[int]:
    """Validate the requested ministry tag ids (tags are optional).

    Returns a de-duplicated list. Raises 400 if any tag does not exist.
    """
    if not tag_ids:
        return []
    ids = list(dict.fromkeys(tag_ids))
    for tid in ids:
        if not session.get(Tag, tid):
            raise HTTPException(status_code=400, detail="Tag not found.")
    return ids


def _set_member_tags(session: Session, member: Member, ids: List[int]) -> None:
    """Replace a member's tag links with the given set of ids."""
    member.tags = [session.get(Tag, tid) for tid in ids]


def _resolve_division_ids(
    session: Session,
    division_id: Optional[int],
    division_ids: Optional[List[int]],
) -> List[int]:
    """Determine the full set of divisions for a member and validate them.

    Falls back to the single primary ``division_id`` when no explicit list is
    given, and always includes the primary division so the member is never
    assigned a primary division it does not also belong to. Raises a 400 if any
    referenced division does not exist.
    """
    ids: List[int] = []
    source = division_ids if division_ids is not None else (
        [division_id] if division_id is not None else []
    )
    for did in source:
        if did is not None and did not in ids:
            ids.append(did)
    # The primary division is always part of the assignment set.
    if division_id is not None and division_id not in ids:
        ids.append(division_id)
    for did in ids:
        if not session.get(Division, did):
            raise HTTPException(status_code=400, detail="Division not found.")
    return ids


def _set_member_divisions(session: Session, member: Member, ids: List[int]) -> None:
    """Replace a member's division links with the given set of ids."""
    member.divisions = [session.get(Division, did) for did in ids]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_default_divisions()
    yield

app = FastAPI(title="Church Management System", lifespan=lifespan)


@app.post("/households", response_model=Household)
def create_household(*, session: Session = Depends(get_session), household: HouseholdCreate):
    db_household = Household.model_validate(household)
    session.add(db_household)
    session.commit()
    session.refresh(db_household)
    return db_household


@app.get("/households", response_model=list[Household])
def list_households(*, session: Session = Depends(get_session)):
    return session.exec(select(Household)).all()


@app.post("/divisions", response_model=Division)
def create_division(*, session: Session = Depends(get_session), division: DivisionCreate):
    db_division = Division.model_validate(division)
    session.add(db_division)
    session.commit()
    session.refresh(db_division)
    return db_division


@app.get("/divisions", response_model=list[Division])
def list_divisions(*, session: Session = Depends(get_session)):
    return session.exec(select(Division)).all()


@app.post("/tags", response_model=Tag)
def create_tag(*, session: Session = Depends(get_session), tag: TagCreate):
    db_tag = Tag.model_validate(tag)
    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return db_tag


@app.get("/tags", response_model=list[Tag])
def list_tags(*, session: Session = Depends(get_session)):
    return session.exec(select(Tag)).all()


@app.post("/members", response_model=MemberRead)
def create_member(*, session: Session = Depends(get_session), member: MemberCreate):
    if not member.first_name.strip() or not member.last_name.strip():
        raise HTTPException(status_code=400, detail="First name and last name are required.")
    if member.email is not None and "@" not in member.email:
        raise HTTPException(status_code=400, detail="Invalid email format.")
    if member.phone is not None and member.phone.strip() and not _is_valid_phone(member.phone):
        raise HTTPException(status_code=400, detail="Invalid phone format.")
    if member.household_id is None:
        raise HTTPException(status_code=400, detail="Household assignment is required.")
    if member.division_id is None:
        raise HTTPException(status_code=400, detail="Division assignment is required.")
    if not session.get(Household, member.household_id):
        raise HTTPException(status_code=400, detail="Household not found.")
    division_ids = _resolve_division_ids(session, member.division_id, member.division_ids)
    tag_ids = _resolve_tag_ids(session, member.tag_ids)
    db_member = Member.model_validate(member, update={"division_ids": None, "tag_ids": None})
    # Add to the session before assigning relationships so the link rows persist
    # cleanly (avoids the "object not in session" autoflush warning).
    session.add(db_member)
    _set_member_divisions(session, db_member, division_ids)
    _set_member_tags(session, db_member, tag_ids)
    session.commit()
    session.refresh(db_member)
    return _to_read(db_member)


@app.get("/members/{member_id}", response_model=MemberRead)
def read_member(*, session: Session = Depends(get_session), member_id: int):
    member = session.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")
    return _to_read(member)


@app.put("/members/{member_id}", response_model=MemberRead)
def update_member(*, session: Session = Depends(get_session), member_id: int, member: MemberUpdate):
    db_member = session.get(Member, member_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found.")
    member_data = member.model_dump(exclude_unset=True)
    # division_ids / tag_ids are handled separately from scalar column assignment.
    new_division_ids = member_data.pop("division_ids", None)
    tag_ids_provided = "tag_ids" in member_data
    new_tag_ids = member_data.pop("tag_ids", None)
    if "email" in member_data and member_data["email"] is not None and "@" not in member_data["email"]:
        raise HTTPException(status_code=400, detail="Invalid email format.")
    if (
        "phone" in member_data
        and member_data["phone"] is not None
        and member_data["phone"].strip()
        and not _is_valid_phone(member_data["phone"])
    ):
        raise HTTPException(status_code=400, detail="Invalid phone format.")
    if "household_id" in member_data and member_data["household_id"] is not None:
        if not session.get(Household, member_data["household_id"]):
            raise HTTPException(status_code=400, detail="Household not found.")
    if "division_id" in member_data and member_data["division_id"] is not None:
        if not session.get(Division, member_data["division_id"]):
            raise HTTPException(status_code=400, detail="Division not found.")
    for key, value in member_data.items():
        setattr(db_member, key, value)
    if new_division_ids is not None:
        # An explicit list fully replaces the member's assignments. Validate
        # each id, then keep the primary division consistent: if the current
        # primary is no longer in the set, retarget it to the first entry.
        for did in new_division_ids:
            if not session.get(Division, did):
                raise HTTPException(status_code=400, detail="Division not found.")
        if new_division_ids and db_member.division_id not in new_division_ids:
            db_member.division_id = new_division_ids[0]
        _set_member_divisions(session, db_member, list(dict.fromkeys(new_division_ids)))
    elif "division_id" in member_data and member_data["division_id"] is not None:
        # Primary division changed without an explicit list: keep the link table
        # in sync so the primary is always part of the member's divisions. Without
        # this the member would be invisible to division-based reads (e.g.
        # attendance-by-division, which counts via MemberDivisionLink).
        existing_ids = [d.id for d in db_member.divisions if d.id is not None]
        if db_member.division_id not in existing_ids:
            existing_ids.append(db_member.division_id)
            _set_member_divisions(session, db_member, existing_ids)
    if tag_ids_provided:
        # An explicit tag_ids list fully replaces tags (an empty list clears them).
        resolved_tags = _resolve_tag_ids(session, new_tag_ids)
        _set_member_tags(session, db_member, resolved_tags)
    session.add(db_member)
    session.commit()
    session.refresh(db_member)
    return _to_read(db_member)


@app.get("/members", response_model=list[MemberRead])
def list_members(
    *,
    session: Session = Depends(get_session),
    q: Optional[str] = Query(default=None),
    household_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    division_id: Optional[int] = Query(default=None),
    tag_id: Optional[int] = Query(default=None),
):
    """List members, optionally narrowed by search and filters (Story 1.3).

    All parameters are optional and combine with AND semantics. With no
    parameters this returns every member (preserving the original behavior).
    """
    statement = select(Member)
    if q:
        # Case-insensitive partial match on first or last name. SQLite LIKE is
        # case-insensitive for ASCII; lower() keeps it explicit and portable.
        pattern = f"%{q.lower()}%"
        statement = statement.where(
            func.lower(Member.first_name).like(pattern)
            | func.lower(Member.last_name).like(pattern)
        )
    if household_id is not None:
        statement = statement.where(Member.household_id == household_id)
    if status is not None:
        statement = statement.where(Member.status == status)
    if division_id is not None:
        # Members assigned to the division via the link table (AC #4).
        statement = statement.join(
            MemberDivisionLink, MemberDivisionLink.member_id == Member.id
        ).where(MemberDivisionLink.division_id == division_id)
    if tag_id is not None:
        # Members assigned the ministry tag via its link table (AC #5).
        statement = statement.join(
            MemberTagLink, MemberTagLink.member_id == Member.id
        ).where(MemberTagLink.tag_id == tag_id)
    members = session.exec(statement).all()
    return [_to_read(m) for m in members]


# --- Attendance (Epic 2, Story 2.1) ----------------------------------------


@app.post("/services", response_model=ServiceRead)
def create_service(*, session: Session = Depends(get_session), service: ServiceCreate):
    db_service = Service.model_validate(service)
    session.add(db_service)
    session.commit()
    session.refresh(db_service)
    return db_service


@app.get("/services", response_model=list[ServiceRead])
def list_services(*, session: Session = Depends(get_session)):
    return session.exec(select(Service)).all()


@app.post("/services/{service_id}/attendance", response_model=list[MemberRead])
def record_attendance(
    *,
    session: Session = Depends(get_session),
    service_id: int,
    attendance: AttendanceCreate,
):
    """Mark one or more members present at a service (AC #2, #3).

    Idempotent: a member already recorded for this service is skipped rather
    than duplicated. Returns the full set of members now present.
    """
    service = session.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found.")
    # Validate every member up front so the whole request fails atomically.
    for member_id in attendance.member_ids:
        if not session.get(Member, member_id):
            raise HTTPException(status_code=400, detail="Member not found.")
    existing = {
        record.member_id
        for record in session.exec(
            select(AttendanceRecord).where(AttendanceRecord.service_id == service_id)
        ).all()
    }
    for member_id in attendance.member_ids:
        if member_id not in existing:
            session.add(
                AttendanceRecord(
                    member_id=member_id, service_id=service_id, date=service.date
                )
            )
            existing.add(member_id)
    session.commit()
    return _present_members(session, service_id)


@app.get("/services/{service_id}/attendance", response_model=list[MemberRead])
def list_service_attendance(*, session: Session = Depends(get_session), service_id: int):
    """Members present at a given service (group/service history, AC #5)."""
    if not session.get(Service, service_id):
        raise HTTPException(status_code=404, detail="Service not found.")
    return _present_members(session, service_id)


@app.get("/members/{member_id}/attendance", response_model=list[AttendanceHistoryEntry])
def member_attendance_history(*, session: Session = Depends(get_session), member_id: int):
    """Services a member attended (per-person history, AC #4)."""
    if not session.get(Member, member_id):
        raise HTTPException(status_code=404, detail="Member not found.")
    records = session.exec(
        select(AttendanceRecord).where(AttendanceRecord.member_id == member_id)
    ).all()
    history = []
    for record in records:
        service = session.get(Service, record.service_id)
        history.append(
            AttendanceHistoryEntry(
                service_id=record.service_id,
                name=service.name if service else "",
                date=record.date,
            )
        )
    return history


def _present_members(session: Session, service_id: int) -> list[MemberRead]:
    """Return the members marked present at a service, as read models."""
    records = session.exec(
        select(AttendanceRecord).where(AttendanceRecord.service_id == service_id)
    ).all()
    members = []
    for record in records:
        member = session.get(Member, record.member_id)
        if member:
            members.append(_to_read(member))
    return members


# --- Division attendance (Epic 2, Story 2.2) -------------------------------


def _division_counts(session: Session, service_id: int) -> list[DivisionAttendanceCount]:
    """Count present members per division for a service (Story 2.2, AC #1, #3).

    Derived purely from existing data: each member marked present at the service
    counts toward every division they belong to (``Member.divisions``). Divisions
    with no present members are omitted. No new data is stored (AD-1, AD-5).
    """
    records = session.exec(
        select(AttendanceRecord).where(AttendanceRecord.service_id == service_id)
    ).all()
    counts: dict[int, int] = {}
    names: dict[int, str] = {}
    for record in records:
        member = session.get(Member, record.member_id)
        if not member:
            continue
        for division in member.divisions:
            if division.id is None:
                continue
            counts[division.id] = counts.get(division.id, 0) + 1
            names[division.id] = division.name
    return [
        DivisionAttendanceCount(
            division_id=did, division_name=names[did], present=present
        )
        for did, present in sorted(counts.items())
    ]


@app.get(
    "/services/{service_id}/attendance/by-division",
    response_model=list[DivisionAttendanceCount],
)
def service_attendance_by_division(
    *, session: Session = Depends(get_session), service_id: int
):
    """Present-member counts grouped by division for a service (AC #1, #3)."""
    if not session.get(Service, service_id):
        raise HTTPException(status_code=404, detail="Service not found.")
    return _division_counts(session, service_id)


@app.get(
    "/divisions/{division_id}/attendance",
    response_model=list[DivisionAttendanceSummaryEntry],
)
def division_attendance_summary(
    *, session: Session = Depends(get_session), division_id: int
):
    """Per-service attendance summary for one division (AC #2).

    For each service this division's members attended, returns the service name,
    date, and the count of that division's members present. Derived from existing
    ``AttendanceRecord`` + division links — no separate store (AD-5).
    """
    division = session.get(Division, division_id)
    if not division:
        # 404: the division named in the path does not exist (matches the
        # service-not-found convention used by the sibling attendance reads).
        raise HTTPException(status_code=404, detail="Division not found.")
    member_ids = {m.id for m in division.assigned_members if m.id is not None}
    if not member_ids:
        return []
    records = session.exec(
        select(AttendanceRecord).where(AttendanceRecord.member_id.in_(member_ids))
    ).all()
    per_service: dict[int, int] = {}
    for record in records:
        per_service[record.service_id] = per_service.get(record.service_id, 0) + 1
    summary = []
    for service_id, present in sorted(per_service.items()):
        service = session.get(Service, service_id)
        if not service:
            continue
        summary.append(
            DivisionAttendanceSummaryEntry(
                service_id=service_id,
                name=service.name,
                date=service.date,
                present=present,
            )
        )
    return summary


# --- Events & RSVPs (Epic 2, Story 2.3) ------------------------------------

# Allowed RSVP responses (AC #2).
_RSVP_RESPONSES = {"yes", "no"}


def _event_summary(session: Session, event_id: int) -> EventRSVPSummary:
    """Yes/no/total RSVP counts for an event (AC #4)."""
    rsvps = session.exec(
        select(EventRSVP).where(EventRSVP.event_id == event_id)
    ).all()
    yes_count = sum(1 for r in rsvps if r.response == "yes")
    no_count = sum(1 for r in rsvps if r.response == "no")
    return EventRSVPSummary(
        event_id=event_id,
        yes_count=yes_count,
        no_count=no_count,
        total=len(rsvps),
    )


@app.post("/events", response_model=EventRead)
def create_event(*, session: Session = Depends(get_session), event: EventCreate):
    db_event = Event.model_validate(event)
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event


@app.get("/events", response_model=list[EventRead])
def list_events(*, session: Session = Depends(get_session)):
    return session.exec(select(Event)).all()


@app.post("/events/{event_id}/rsvps", response_model=EventRSVPSummary)
def create_or_update_rsvp(
    *, session: Session = Depends(get_session), event_id: int, rsvp: RSVPCreate
):
    """Record or update a member's RSVP to an event (AC #2, #3).

    Idempotent per (member, event): re-RSVPing updates the existing response
    rather than inserting a duplicate. Returns the event's attendee summary.
    """
    if not session.get(Event, event_id):
        raise HTTPException(status_code=404, detail="Event not found.")
    if not session.get(Member, rsvp.member_id):
        raise HTTPException(status_code=400, detail="Member not found.")
    if rsvp.response not in _RSVP_RESPONSES:
        raise HTTPException(status_code=400, detail="Response must be 'yes' or 'no'.")
    existing = session.exec(
        select(EventRSVP)
        .where(EventRSVP.event_id == event_id)
        .where(EventRSVP.member_id == rsvp.member_id)
    ).first()
    if existing:
        existing.response = rsvp.response
        session.add(existing)
    else:
        session.add(
            EventRSVP(
                event_id=event_id, member_id=rsvp.member_id, response=rsvp.response
            )
        )
    session.commit()
    return _event_summary(session, event_id)


@app.get("/events/{event_id}/rsvps", response_model=list[RSVPRead])
def list_event_rsvps(*, session: Session = Depends(get_session), event_id: int):
    """All RSVPs recorded for an event (AC #4)."""
    if not session.get(Event, event_id):
        raise HTTPException(status_code=404, detail="Event not found.")
    rsvps = session.exec(
        select(EventRSVP).where(EventRSVP.event_id == event_id)
    ).all()
    return [RSVPRead(member_id=r.member_id, response=r.response) for r in rsvps]


@app.get("/events/{event_id}/summary", response_model=EventRSVPSummary)
def event_summary(*, session: Session = Depends(get_session), event_id: int):
    """Attendee-count summary for an event (AC #4)."""
    if not session.get(Event, event_id):
        raise HTTPException(status_code=404, detail="Event not found.")
    return _event_summary(session, event_id)


# --- Giving (Epic 3, Story 3.1) --------------------------------------------


@app.post("/donations", response_model=DonationRead)
def create_donation(*, session: Session = Depends(get_session), donation: DonationCreate):
    if donation.amount <= 0:
        raise HTTPException(status_code=400, detail="Donation amount must be positive.")
    if not donation.donation_type.strip():
        raise HTTPException(status_code=400, detail="Donation type is required.")
    if donation.member_id is None and donation.household_id is None:
        raise HTTPException(
            status_code=400, detail="A donation must reference a member or household."
        )
    if donation.member_id is not None and not session.get(Member, donation.member_id):
        raise HTTPException(status_code=400, detail="Member not found.")
    if donation.household_id is not None and not session.get(
        Household, donation.household_id
    ):
        raise HTTPException(status_code=400, detail="Household not found.")
    db_donation = Donation.model_validate(donation)
    session.add(db_donation)
    session.commit()
    session.refresh(db_donation)
    return db_donation


@app.get("/donations", response_model=list[DonationRead])
def list_donations(*, session: Session = Depends(get_session)):
    return session.exec(select(Donation)).all()


@app.get("/members/{member_id}/donations", response_model=list[DonationRead])
def member_donations(*, session: Session = Depends(get_session), member_id: int):
    """A member's giving history (AC #3)."""
    if not session.get(Member, member_id):
        raise HTTPException(status_code=404, detail="Member not found.")
    return session.exec(
        select(Donation).where(Donation.member_id == member_id)
    ).all()


@app.get("/households/{household_id}/donations", response_model=list[DonationRead])
def household_donations(*, session: Session = Depends(get_session), household_id: int):
    """A household's giving history (AC #3)."""
    if not session.get(Household, household_id):
        raise HTTPException(status_code=404, detail="Household not found.")
    return session.exec(
        select(Donation).where(Donation.household_id == household_id)
    ).all()


@app.get("/", include_in_schema=False)
def serve_app():
    return FileResponse(STATIC_DIR / "index.html")


# Serve the rest of the single-page UI assets (CSS/JS) if any are added later.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
