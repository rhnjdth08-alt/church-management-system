from datetime import date
from typing import List, Optional

from sqlmodel import SQLModel


class HouseholdCreate(SQLModel):
    name: str
    address: Optional[str] = None


class DivisionCreate(SQLModel):
    name: str
    description: Optional[str] = None


class TagCreate(SQLModel):
    name: str
    description: Optional[str] = None


class MemberCreate(SQLModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "active"
    household_id: Optional[int] = None
    division_id: Optional[int] = None
    # One or more divisions (AC #1). When omitted, division_id is used.
    division_ids: Optional[List[int]] = None
    # Zero or more ministry tags.
    tag_ids: Optional[List[int]] = None


class MemberUpdate(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    household_id: Optional[int] = None
    division_id: Optional[int] = None
    # Replace the member's division assignments when provided (AC #1).
    division_ids: Optional[List[int]] = None
    # Replace the member's ministry tags when provided.
    tag_ids: Optional[List[int]] = None


class MemberRead(SQLModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "active"
    household_id: Optional[int] = None
    division_id: Optional[int] = None
    # Flattened assigned division ids for directory/profile views (AC #3, #4).
    division_ids: List[int] = []
    # Flattened assigned ministry tag ids.
    tag_ids: List[int] = []


# --- Attendance (Epic 2) ---------------------------------------------------


class ServiceCreate(SQLModel):
    name: str
    date: date


class ServiceRead(SQLModel):
    id: int
    name: str
    date: date


class AttendanceCreate(SQLModel):
    # Members to mark present for the service.
    member_ids: List[int] = []


class AttendanceHistoryEntry(SQLModel):
    """One row of a member's attendance history (per-person view, AC #4)."""

    service_id: int
    name: str
    date: date


# --- Division attendance (Story 2.2) ---------------------------------------


class DivisionAttendanceCount(SQLModel):
    """Present-member count for one division at a service (Story 2.2, AC #1, #3)."""

    division_id: int
    division_name: str
    present: int


class DivisionAttendanceSummaryEntry(SQLModel):
    """One service in a division's attendance summary (Story 2.2, AC #2)."""

    service_id: int
    name: str
    date: date
    present: int


# --- Events & RSVPs (Story 2.3) --------------------------------------------


class EventCreate(SQLModel):
    name: str
    date: date
    location: Optional[str] = None
    description: Optional[str] = None


class EventRead(SQLModel):
    id: int
    name: str
    date: date
    location: Optional[str] = None
    description: Optional[str] = None


class RSVPCreate(SQLModel):
    member_id: int
    response: str


class RSVPRead(SQLModel):
    member_id: int
    response: str


class EventRSVPSummary(SQLModel):
    """Attendee-count breakdown for an event (Story 2.3, AC #4)."""

    event_id: int
    yes_count: int
    no_count: int
    total: int
