from sqlmodel import SQLModel, Session, text
from app.db.engine import engine

import app.models


def init_db():
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.exec(text("PRAGMA journal_mode=WAL;"))
        session.exec(text("PRAGMA synchronous=NORMAL;"))
