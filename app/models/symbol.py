from sqlmodel import SQLModel, Field


class Symbol(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, unique=True)
    name: str
    exchange: str = "NSE"
