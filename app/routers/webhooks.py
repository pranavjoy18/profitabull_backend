from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.daily_screener_status import DailyScreenerStatus
from app.models.screener import Screener
from app.models.screener_event import ScreenerEvent
from app.models.symbol import Symbol
from app.schemas.chartink import ChartinkWebhookPayload
from app.utils import parse_trigger_time

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/chartink")
def chartink_webhook(
    payload: ChartinkWebhookPayload,
    session: Session = Depends(get_session),
):
    today = date.today()

    # 1️⃣ Resolve screener
    screener = session.exec(
        select(Screener).where(Screener.slug == payload.scan_url)
    ).first()

    if not screener:
        screener = Screener(
            name=payload.scan_name,
            slug=payload.scan_url,
            source="chartink",
        )
        session.add(screener)
        session.commit()
        session.refresh(screener)

    # 2️⃣ Split stocks & prices
    symbols = [s.strip() for s in payload.stocks.split(",") if s.strip()]
    prices = (
        [float(p) for p in payload.trigger_prices.split(",")]
        if payload.trigger_prices
        else [None] * len(symbols)
    )

    trigger_time = parse_trigger_time(payload.triggered_at)

    # 3️⃣ Process each symbol
    for symbol_str, price in zip(symbols, prices):
        # Resolve symbol
        symbol = session.exec(
            select(Symbol).where(Symbol.symbol == symbol_str)
        ).first()

        if not symbol:
            symbol = Symbol(symbol=symbol_str, name=symbol_str)
            session.add(symbol)
            session.commit()
            session.refresh(symbol)

        # 4️⃣ Insert raw screener event
        event = ScreenerEvent(
            screener_id=screener.id,
            symbol_id=symbol.id,
            trigger_price=price,
            triggered_at_time=trigger_time,
            trade_date=today,
            raw_payload=payload.dict(),
        )
        session.add(event)

        # 5️⃣ Upsert daily screener status
        status = session.exec(
            select(DailyScreenerStatus).where(
                DailyScreenerStatus.symbol_id == symbol.id,
                DailyScreenerStatus.screener_id == screener.id,
                DailyScreenerStatus.trade_date == today,
            )
        ).first()

        now = datetime.now(timezone.utc)

        if status:
            status.trigger_count += 1
            status.last_triggered_at = now
        else:
            status = DailyScreenerStatus(
                symbol_id=symbol.id,
                screener_id=screener.id,
                trade_date=today,
                first_triggered_at=now,
                last_triggered_at=now,
            )
            session.add(status)

    session.commit()

    return {"status": "ok"}
