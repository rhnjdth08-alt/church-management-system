from typing import Optional

from sqlmodel import SQLModel


class HouseholdCreate(SQLModel):
    name: str
    address: Optional[str] = None


class DivisionCreate(SQLModel):
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


class MemberUpdate(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    household_id: Optional[int] = None
    division_id: Optional[int] = None
