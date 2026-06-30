from datetime import datetime

from pydantic import BaseModel, Field


class ExchangeRule(BaseModel):
    id: int | None = None
    name: str = Field(..., min_length=1, max_length=100)
    brand: str
    support_bar: bool = True
    support_other_brand: bool = True
    support_old_jewelry: bool = True
    need_extra_gold: bool = False
    extra_rate: float = Field(default=0, ge=0)
    loss_type: str = Field(default="fixed", pattern="^(fixed|percentage)$")
    loss_value: float = Field(default=0, ge=0)
    labor_type: str = Field(default="perGram", pattern="^(fixed|perGram)$")
    labor_value: float = Field(default=0, ge=0)
    recycle_price_type: str = Field(default="recycle", pattern="^(recycle|jewelry)$")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExchangeRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    brand: str
    support_bar: bool = True
    support_other_brand: bool = True
    support_old_jewelry: bool = True
    need_extra_gold: bool = False
    extra_rate: float = Field(default=0, ge=0)
    loss_type: str = Field(default="fixed", pattern="^(fixed|percentage)$")
    loss_value: float = Field(default=0, ge=0)
    labor_type: str = Field(default="perGram", pattern="^(fixed|perGram)$")
    labor_value: float = Field(default=0, ge=0)
    recycle_price_type: str = Field(default="recycle", pattern="^(recycle|jewelry)$")
