from datetime import date, datetime
from sqlmodel import SQLModel, Field


class DailyScreenerStatus(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    symbol_id: int = Field(foreign_key="symbol.id", index=True)
    screener_id: int = Field(foreign_key="screener.id", index=True)

    trade_date: date = Field(index=True)

    triggered: bool = Field(default=True)

    trigger_count: int = Field(default=1)
    first_triggered_at: datetime | None = None
    last_triggered_at: datetime | None = None
