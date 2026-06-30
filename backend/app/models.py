from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


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
    members: List["Member"] = Relationship(back_populates="division")


class DivisionCreate(DivisionBase):
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
    division: Optional[Division] = Relationship(back_populates="members")


class MemberCreate(MemberBase):
    pass


class MemberRead(MemberBase):
    id: int


class MemberUpdate(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    household_id: Optional[int] = None
    division_id: Optional[int] = None
