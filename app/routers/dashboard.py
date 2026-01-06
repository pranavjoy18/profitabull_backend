from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.daily_screener_status import DailyScreenerStatus
from app.models.index import Index
from app.models.index_constituent import IndexConstituent
from app.models.screener import Screener
from app.models.symbol import Symbol


router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("")
def dashboard_view(
    index: str = Query(...),
    trade_date: date = Query(default=date.today()),
    session: Session = Depends(get_session),
):
    # 1️⃣ Resolve index
    idx = session.exec(
        select(Index).where(Index.name == index)
    ).first()

    if not idx:
        return {"index": index, "rows": []}

    # 2️⃣ Get index constituents
    constituents = session.exec(
        select(IndexConstituent, Symbol)
        .where(IndexConstituent.index_id == idx.id)
        .where(Symbol.id == IndexConstituent.symbol_id)
    ).all()

    symbol_ids = [sym.id for _, sym in constituents]

    # 3️⃣ Fetch active screeners
    screeners = session.exec(
        select(Screener).where(Screener.active == True)
    ).all()

    screener_ids = [s.id for s in screeners]

    # 4️⃣ Fetch daily screener statuses
    statuses = session.exec(
        select(DailyScreenerStatus)
        .where(DailyScreenerStatus.trade_date == trade_date)
        .where(DailyScreenerStatus.symbol_id.in_(symbol_ids))
        .where(DailyScreenerStatus.screener_id.in_(screener_ids))
    ).all()

    # 5️⃣ Pivot screener status → lookup dict
    status_map = {}
    for s in statuses:
        status_map[(s.symbol_id, s.screener_id)] = True

    # 6️⃣ Build rows
    rows = []
    for constituent, symbol in constituents:
        row = {
            "symbol": symbol.symbol,
            "weightage": constituent.weightage,
            # NSE data will come later
            "day_close": None,
            "day_change_pct": None,
            "screeners": {
                str(s.id): status_map.get((symbol.id, s.id), False)
                for s in screeners
            },
        }
        rows.append(row)

    return {
        "index": idx.name,
        "date": trade_date.isoformat(),
        "screeners": [
            {"id": s.id, "name": s.name} for s in screeners
        ],
        "rows": rows,
    }

