import asyncio
from datetime import date
from typing import Iterable

from sqlmodel import Session, select

from app.db.engine import engine
from app.models.daily_symbol_snapshot import DailySymbolSnapshot
from app.models.symbol import Symbol
from app.nse.nse import fetch_eod_data
from app.utils import time_async



def _upsert_snapshot(
    session: Session,
    *,
    symbol_id: int,
    trade_date: date,
    nse_data,
) -> None:
    snapshot = session.exec(
        select(DailySymbolSnapshot).where(
            DailySymbolSnapshot.symbol_id == symbol_id,
            DailySymbolSnapshot.trade_date == trade_date,
        )
    ).first()

    if snapshot:
        snapshot.close_price = nse_data.close
        snapshot.change_pct = nse_data.day_change_pct
        snapshot.volume = int(nse_data.total_volume)
        snapshot.extra_data = {
            "year_high": nse_data.year_high,
            "year_low": nse_data.year_low,
            "delivery_volume": nse_data.delivery_volume,
            "delivery_pct": nse_data.delivery_pct,
        }
    else:
        snapshot = DailySymbolSnapshot(
            symbol_id=symbol_id,
            trade_date=trade_date,
            close_price=nse_data.close,
            change_pct=nse_data.day_change_pct,
            volume=int(nse_data.total_volume),
            extra_data={
                "year_high": nse_data.year_high,
                "year_low": nse_data.year_low,
                "delivery_volume": nse_data.delivery_volume,
                "delivery_pct": nse_data.delivery_pct,
            },
        )
        session.add(snapshot)


@time_async("NSE EOD snapshot ingestion")
async def ingest_nse_eod_snapshots(
    *,
    trade_date: date | None = None,
    symbols: Iterable[str] | None = None,
) -> None:
    """
    Fetch NSE EOD data and upsert DailySymbolSnapshot rows.

    - If symbols is None → fetch all symbols from DB
    - trade_date defaults to today
    """
    trade_date = trade_date or date.today()

    with Session(engine) as session:
        # 1️⃣ Resolve symbols
        if symbols is None:
            db_symbols = session.exec(select(Symbol)).all()
            symbol_map = {s.symbol: s for s in db_symbols}
        else:
            db_symbols = session.exec(
                select(Symbol).where(Symbol.symbol.in_(symbols))
            ).all()
            symbol_map = {s.symbol: s for s in db_symbols}

    if not symbol_map:
        print("⚠️ No symbols found for NSE ingestion")
        return

    # 2️⃣ Fetch NSE data
    nse_results = await fetch_eod_data(list(symbol_map.keys()))

    if not nse_results:
        print("⚠️ NSE returned no data")
        return

    # 3️⃣ Upsert snapshots
    with Session(engine) as session:
        for symbol, nse_data in nse_results.items():
            db_symbol = symbol_map.get(symbol)
            if not db_symbol:
                continue  # should not happen, but safe

            _upsert_snapshot(
                session,
                symbol_id=db_symbol.id,
                trade_date=trade_date,
                nse_data=nse_data,
            )

        session.commit()

    print(f"✅ NSE EOD snapshots ingested for {len(nse_results)} symbols")

if __name__ == "__main__":
    asyncio.run(ingest_nse_eod_snapshots())