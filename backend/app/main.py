from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from .database import create_db_and_tables, get_session
from .models import Division, Household, Member
from .schemas import DivisionCreate, HouseholdCreate, MemberCreate, MemberUpdate


@asynccontextmanager
def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Church Management System", lifespan=lifespan)


@app.post("/households", response_model=Household)
def create_household(*, session: Session = Depends(get_session), household: HouseholdCreate):
    db_household = Household.model_validate(household)
    session.add(db_household)
    session.commit()
    session.refresh(db_household)
    return db_household


@app.post("/divisions", response_model=Division)
def create_division(*, session: Session = Depends(get_session), division: DivisionCreate):
    db_division = Division.model_validate(division)
    session.add(db_division)
    session.commit()
    session.refresh(db_division)
    return db_division


@app.post("/members", response_model=Member)
def create_member(*, session: Session = Depends(get_session), member: MemberCreate):
    if not member.first_name.strip() or not member.last_name.strip():
        raise HTTPException(status_code=400, detail="First name and last name are required.")
    if member.email is not None and "@" not in member.email:
        raise HTTPException(status_code=400, detail="Invalid email format.")
    if member.household_id is None:
        raise HTTPException(status_code=400, detail="Household assignment is required.")
    if member.division_id is None:
        raise HTTPException(status_code=400, detail="Division assignment is required.")
    if not session.get(Household, member.household_id):
        raise HTTPException(status_code=400, detail="Household not found.")
    if not session.get(Division, member.division_id):
        raise HTTPException(status_code=400, detail="Division not found.")
    db_member = Member.model_validate(member)
    session.add(db_member)
    session.commit()
    session.refresh(db_member)
    return db_member


@app.get("/members/{member_id}", response_model=Member)
def read_member(*, session: Session = Depends(get_session), member_id: int):
    member = session.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")
    return member


@app.put("/members/{member_id}", response_model=Member)
def update_member(*, session: Session = Depends(get_session), member_id: int, member: MemberUpdate):
    db_member = session.get(Member, member_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found.")
    member_data = member.model_dump(exclude_unset=True)
    if "email" in member_data and member_data["email"] is not None and "@" not in member_data["email"]:
        raise HTTPException(status_code=400, detail="Invalid email format.")
    if "household_id" in member_data and member_data["household_id"] is not None:
        if not session.get(Household, member_data["household_id"]):
            raise HTTPException(status_code=400, detail="Household not found.")
    if "division_id" in member_data and member_data["division_id"] is not None:
        if not session.get(Division, member_data["division_id"]):
            raise HTTPException(status_code=400, detail="Division not found.")
    for key, value in member_data.items():
        setattr(db_member, key, value)
    session.add(db_member)
    session.commit()
    session.refresh(db_member)
    return db_member


@app.get("/members", response_model=list[Member])
def list_members(*, session: Session = Depends(get_session)):
    members = session.exec(select(Member)).all()
    return members
