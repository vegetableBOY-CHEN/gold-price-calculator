from datetime import datetime

from pydantic import BaseModel, Field


class GoldPriceItem(BaseModel):
    brand: str
    brand_name: str
    gold_price: float = Field(ge=0)
    bar_price: float | None = Field(default=None, ge=0)
    update_time: datetime | None = None


class DomesticGoldPrice(BaseModel):
    price: float = Field(ge=0)
    update_time: datetime | None = None


class MarketGoldPrice(BaseModel):
    market: str
    name: str
    symbol: str
    exchange: str | None = None
    price: float = Field(ge=0)
    currency: str = "CNY"
    unit: str = "g"
    change: float | None = None
    change_percent: float | None = None
    source: str = "local"
    status: str = "fallback"
    update_time: datetime | None = None


class GoldPriceOverview(BaseModel):
    domestic: DomesticGoldPrice
    international: list[MarketGoldPrice] = []
    domestic_markets: list[MarketGoldPrice] = []
    brands: list[GoldPriceItem]
    brand_refresh_interval_seconds: int = 28800
    market_refresh_interval_seconds: int = 5
    server_time: datetime | None = None


class GoldPriceUpdate(BaseModel):
    domestic_price: float | None = Field(default=None, ge=0)
    brands: list[GoldPriceItem] | None = None
