from datetime import datetime,timezone
from sqlmodel import SQLModel, Field


class Screener(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    name: str
    slug: str = Field(index=True, unique=True)  # scan_url from Chartink
    source: str = Field(default="chartink")

    active: bool = Field(default=True)

    created_at: datetime = Field(default_factory= lambda : datetime.now(timezone.utc))
