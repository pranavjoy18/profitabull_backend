from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.screener import Screener

router = APIRouter(prefix="/screeners", tags=["screeners"])


@router.get("")
def list_screeners(session: Session = Depends(get_session)):
    screeners = session.exec(
        select(Screener).where(Screener.active == True)
    ).all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
        }
        for s in screeners
    ]
