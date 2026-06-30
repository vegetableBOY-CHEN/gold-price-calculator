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


class GoldPriceOverview(BaseModel):
    domestic: DomesticGoldPrice
    brands: list[GoldPriceItem]


class GoldPriceUpdate(BaseModel):
    domestic_price: float | None = Field(default=None, ge=0)
    brands: list[GoldPriceItem] | None = None
