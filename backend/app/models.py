from datetime import date
from typing import List, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class MemberDivisionLink(SQLModel, table=True):
    """Association table giving each member one or more divisions (AC #1)."""

    member_id: Optional[int] = Field(
        default=None, foreign_key="member.id", primary_key=True
    )
    division_id: Optional[int] = Field(
        default=None, foreign_key="division.id", primary_key=True
    )


class MemberTagLink(SQLModel, table=True):
    """Association table giving each member zero or more ministry tags."""

    member_id: Optional[int] = Field(
        default=None, foreign_key="member.id", primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="tag.id", primary_key=True
    )


class HouseholdBase(SQLModel):
    name: str
    address: Optional[str] = None


class Household(HouseholdBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    members: List["Member"] = Relationship(back_populates="household")


class HouseholdCreate(HouseholdBase):
    pass


class DivisionBase(SQLModel):
    name: str
    description: Optional[str] = None


class Division(DivisionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Members whose *primary* division is this one (legacy single assignment).
    members: List["Member"] = Relationship(back_populates="division")
    # Members assigned to this division via the many-to-many link (AC #1).
    assigned_members: List["Member"] = Relationship(
        back_populates="divisions", link_model=MemberDivisionLink
    )


class DivisionCreate(DivisionBase):
    pass


class TagBase(SQLModel):
    name: str
    description: Optional[str] = None


class Tag(TagBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Members assigned this ministry tag (many-to-many).
    members: List["Member"] = Relationship(
        back_populates="tags", link_model=MemberTagLink
    )


class TagCreate(TagBase):
    pass


class MemberBase(SQLModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "active"
    household_id: Optional[int] = Field(default=None, foreign_key="household.id")
    division_id: Optional[int] = Field(default=None, foreign_key="division.id")


class Member(MemberBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    household: Optional[Household] = Relationship(back_populates="members")
    # Primary division (legacy single assignment, kept for compatibility).
    division: Optional[Division] = Relationship(
        back_populates="members",
        sa_relationship_kwargs={"foreign_keys": "Member.division_id"},
    )
    # All assigned divisions (AC #1: one or more).
    divisions: List[Division] = Relationship(
        back_populates="assigned_members", link_model=MemberDivisionLink
    )
    # Optional ministry tags (zero or more).
    tags: List[Tag] = Relationship(
        back_populates="members", link_model=MemberTagLink
    )


class MemberCreate(MemberBase):
    # Optional list of divisions; when omitted the primary division_id is used.
    division_ids: Optional[List[int]] = None
    # Optional list of ministry tags.
    tag_ids: Optional[List[int]] = None


class MemberRead(MemberBase):
    id: int
    # Flattened list of assigned division ids for API responses (AC #3, #4).
    division_ids: List[int] = []
    # Flattened list of assigned ministry tag ids.
    tag_ids: List[int] = []


class MemberUpdate(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    household_id: Optional[int] = None
    division_id: Optional[int] = None
    division_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None


# --- Attendance (Epic 2) ---------------------------------------------------


class ServiceBase(SQLModel):
    name: str
    # ISO date string of the service/event (e.g. "2026-07-05").
    date: date


class Service(ServiceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    attendance: List["AttendanceRecord"] = Relationship(back_populates="service")


class ServiceCreate(ServiceBase):
    pass


class AttendanceRecord(SQLModel, table=True):
    """One member marked present at one service.

    A unique (member_id, service_id) pair keeps recording idempotent. The
    service ``date`` is denormalized here for convenient per-person history.
    """

    __table_args__ = (
        UniqueConstraint("member_id", "service_id", name="uq_attendance_member_service"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: int = Field(foreign_key="member.id")
    service_id: int = Field(foreign_key="service.id")
    date: date

    service: Optional[Service] = Relationship(back_populates="attendance")


# --- Events & RSVPs (Epic 2, Story 2.3) ------------------------------------


class EventBase(SQLModel):
    name: str
    # ISO date string of the event (e.g. "2026-08-01").
    date: date
    location: Optional[str] = None
    description: Optional[str] = None


class Event(EventBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rsvps: List["EventRSVP"] = Relationship(back_populates="event")


class EventRSVP(SQLModel, table=True):
    """One member's RSVP to one event.

    A unique (member_id, event_id) pair keeps RSVPing idempotent — re-RSVPing
    updates the existing ``response`` rather than inserting a duplicate.
    ``response`` is "yes" or "no".
    """

    __table_args__ = (
        UniqueConstraint("member_id", "event_id", name="uq_rsvp_member_event"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: int = Field(foreign_key="member.id")
    event_id: int = Field(foreign_key="event.id")
    response: str

    event: Optional[Event] = Relationship(back_populates="rsvps")
