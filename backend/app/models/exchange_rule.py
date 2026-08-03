from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ExchangeRule(BaseModel):
    id: int | None = None
    name: str = Field(..., min_length=1, max_length=100)
    brand: str
    store_name: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)
    support_bar: bool = True
    support_other_brand: bool = True
    support_old_jewelry: bool = True
    need_extra_gold: bool = False
    extra_rate: float = Field(default=0, ge=0)
    loss_type: Literal["percentage"] = "percentage"
    loss_value: float = Field(default=0, ge=0, le=100)
    labor_type: str = Field(default="perGram", pattern="^(fixed|perGram)$")
    labor_value: float = Field(default=0, ge=0)
    recycle_price_type: str = Field(default="recycle", pattern="^(recycle|jewelry)$")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_extra_rate(self):
        if self.need_extra_gold and self.extra_rate <= 0:
            raise ValueError("要求增金时，增金比例必须大于 0")
        if not self.need_extra_gold:
            self.extra_rate = 0
        return self


class ExchangeRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    brand: str
    store_name: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)
    support_bar: bool = True
    support_other_brand: bool = True
    support_old_jewelry: bool = True
    need_extra_gold: bool = False
    extra_rate: float = Field(default=0, ge=0)
    loss_type: Literal["percentage"] = "percentage"
    loss_value: float = Field(default=0, ge=0, le=100)
    labor_type: str = Field(default="perGram", pattern="^(fixed|perGram)$")
    labor_value: float = Field(default=0, ge=0)
    recycle_price_type: str = Field(default="recycle", pattern="^(recycle|jewelry)$")

    @model_validator(mode="after")
    def validate_extra_rate(self):
        if self.need_extra_gold and self.extra_rate <= 0:
            raise ValueError("要求增金时，增金比例必须大于 0")
        if not self.need_extra_gold:
            self.extra_rate = 0
        return self
