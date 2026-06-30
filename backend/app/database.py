from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine  # type: ignore[import]

from .models import Member  # ensure model metadata is registered before table creation

DB_PATH = Path(__file__).resolve().parents[1] / "church.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
