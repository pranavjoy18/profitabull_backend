from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.index import Index

router = APIRouter(prefix="/indices", tags=["indices"])


@router.get("")
def list_indices(session: Session = Depends(get_session)):
    indices = session.exec(select(Index)).all()
    return [
        {
            "id": idx.id,
            "name": idx.name,
            "description": idx.description,
        }
        for idx in indices
    ]
