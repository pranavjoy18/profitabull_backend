from sqlmodel import SQLModel, Field


class IndexConstituent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    index_id: int = Field(foreign_key="index.id")
    symbol_id: int = Field(foreign_key="symbol.id")
    weightage: float
