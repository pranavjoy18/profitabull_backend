from datetime import datetime, date, time, timezone
from typing import Any
from sqlmodel import SQLModel, Field
from sqlalchemy import JSON, Column


class ScreenerEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    screener_id: int = Field(foreign_key="screener.id", index=True)
    symbol_id: int = Field(foreign_key="symbol.id", index=True)

    trigger_price: float | None = None
    triggered_at_time: time | None = None
    trade_date: date = Field(index=True)

    raw_payload: dict[str,Any] = Field(sa_column=Column(JSON))

    created_at: datetime = Field(default_factory= lambda : datetime.now(timezone.utc))
