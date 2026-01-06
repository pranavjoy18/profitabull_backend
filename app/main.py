from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from sqlmodel import Session, select

from app.db.init_db import init_db

from app.db.session import get_session
from app.models.symbol import Symbol
from app.routers.webhooks import router as webhook_router
from app.routers.indices import router as indices_router
from app.routers.screeners import router as screeners_router
from app.routers.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Profitabull API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(webhook_router)
app.include_router(indices_router)
app.include_router(screeners_router)
app.include_router(dashboard_router)


@app.get("/symbols")
def get_symbols(session: Session = Depends(get_session)):
    return session.exec(select(Symbol)).all()

@app.get("/health")
def health_check():
    return {"status": "ok"}
