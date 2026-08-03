from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PurchaseInfo(BaseModel):
    brand: str
    new_weight: float = Field(..., gt=0, description="新金重量(g)")
    new_price: float = Field(..., gt=0, description="金价(元/g)")
    labor_fee: float | None = Field(default=None, ge=0, description="工费，留空则按规则计算")
    old_weight: float = Field(default=0, ge=0, description="旧金重量(g)")
    old_purchase_cost: float = Field(default=0, ge=0, description="旧金购买成本")
    old_brand: str | None = Field(default=None, description="旧金品牌")
    old_is_bar: bool = Field(default=False, description="是否金条")
    recycle_price: float | None = Field(default=None, ge=0, description="回收价，留空则自动推算")


class CostCalculationRequest(BaseModel):
    purchase: PurchaseInfo
    rule_id: int | None = Field(default=None, description="门店规则模板 ID")
    exchange_rule: "ExchangeRuleInline | None" = Field(default=None, description="临时规则，优先于模板")


class ExchangeRuleInline(BaseModel):
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


class CostBreakdownItem(BaseModel):
    label: str
    value: float
    detail: str | None = None


class CostCalculationResult(BaseModel):
    brand: str
    new_gold_total: float
    labor_fee: float
    old_weight: float
    loss_amount: float
    exchangeable_weight: float
    recycle_price: float
    old_gold_deduction: float
    direct_purchase_cost: float
    actual_cost: float
    savings_amount: float
    final_cost: float
    price_per_gram: float
    min_new_weight: float | None = None
    breakdown: list[CostBreakdownItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


CostCalculationRequest.model_rebuild()
