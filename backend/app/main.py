from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import calculate, exchange_rules, health, prices
from app.db.database import SessionLocal, init_db
from app.services.exchange_rule_service import ExchangeRuleService
from app.services.gold_price_service import GoldPriceService

settings = get_settings()


def seed_database():
    db = SessionLocal()
    try:
        GoldPriceService(db).seed_if_empty()
        ExchangeRuleService(db).seed_if_empty()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_database()
    yield


app = FastAPI(
    title=settings.app_name,
    description="金饰购买成本计算 API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(prices.router, prefix="/api/prices", tags=["prices"])
app.include_router(exchange_rules.router, prefix="/api/rules", tags=["rules"])
app.include_router(calculate.router, prefix="/api/calculate", tags=["calculate"])
