from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON


class DailySymbolSnapshot(SQLModel, table=True):
    """
    One row per (symbol_id, trade_date)

    Represents immutable EOD market data for a symbol.
    Idempotency is handled in ingestion code, NOT via DB constraints.
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    # --- Foreign keys ---
    symbol_id: int = Field(
        foreign_key="symbol.id",
        index=True,
        description="FK to symbol table",
    )

    # --- Time dimension ---
    trade_date: date = Field(
        index=True,
        description="Trading date for this snapshot",
    )

    # --- Core EOD metrics (frequently queried) ---
    close_price: Optional[float] = Field(
        default=None,
        description="EOD close price",
    )

    change_pct: Optional[float] = Field(
        default=None,
        description="Day change percentage",
    )

    volume: Optional[int] = Field(
        default=None,
        description="Total traded volume",
    )

    # --- Flexible NSE fields ---
    extra_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Additional NSE fields (year high/low, delivery stats, etc.)",
    )

    # --- Metadata ---
    created_at: datetime = Field(
        default_factory=lambda : datetime.now(timezone.utc),
        description="Row creation timestamp",
    )

