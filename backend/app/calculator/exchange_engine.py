from app.models.exchange_rule import ExchangeRule
from app.models.purchase import (
    CostBreakdownItem,
    CostCalculationRequest,
    CostCalculationResult,
    ExchangeRuleInline,
    PurchaseInfo,
)


class ExchangeCalculator:
    """金饰置换成本计算引擎"""

    def calculate(
        self,
        purchase: PurchaseInfo,
        rule: ExchangeRule | ExchangeRuleInline,
    ) -> CostCalculationResult:
        warnings: list[str] = []

        if purchase.old_weight > 0:
            if purchase.old_is_bar and not rule.support_bar:
                raise ValueError("该门店不支持金条置换")
            if (
                purchase.old_brand
                and purchase.old_brand != purchase.brand
                and not rule.support_other_brand
            ):
                raise ValueError("该门店不支持跨品牌置换")
            if not rule.support_old_jewelry and not purchase.old_is_bar:
                raise ValueError("该门店不支持旧饰品置换")

        loss_amount = self._calc_loss(purchase.old_weight, rule.loss_type, rule.loss_value)
        exchangeable_weight = max(0.0, round(purchase.old_weight - loss_amount, 4))

        min_new_weight: float | None = None
        if purchase.old_weight > 0 and rule.need_extra_gold and rule.extra_rate > 0:
            min_new_weight = round(purchase.old_weight * (1 + rule.extra_rate / 100), 4)
            if purchase.new_weight < min_new_weight:
                warnings.append(
                    f"增金要求：新金重量应不少于 {min_new_weight:.2f}g（当前 {purchase.new_weight}g）"
                )

        recycle_price = self._resolve_recycle_price(purchase, rule)
        old_deduction = round(exchangeable_weight * recycle_price, 2) if exchangeable_weight > 0 else 0.0

        new_gold_total = round(purchase.new_weight * purchase.new_price, 2)
        labor_fee = self._calc_labor(purchase, rule)
        final_cost = round(new_gold_total + labor_fee - old_deduction, 2)
        price_per_gram = round(final_cost / purchase.new_weight, 2) if purchase.new_weight > 0 else 0.0

        breakdown = [
            CostBreakdownItem(
                label="新金总价",
                value=new_gold_total,
                detail=f"{purchase.new_weight}g × ¥{purchase.new_price}/g",
            ),
            CostBreakdownItem(label="工费", value=labor_fee),
        ]
        if purchase.old_weight > 0:
            breakdown.extend([
                CostBreakdownItem(
                    label="旧金重量",
                    value=purchase.old_weight,
                    detail=f"{'金条' if purchase.old_is_bar else '饰品'}",
                ),
                CostBreakdownItem(label="损耗", value=loss_amount, detail=self._loss_desc(rule)),
                CostBreakdownItem(
                    label="可抵扣重量",
                    value=exchangeable_weight,
                    detail=f"× ¥{recycle_price}/g",
                ),
                CostBreakdownItem(label="旧金抵扣", value=-old_deduction),
            ])
        breakdown.append(CostBreakdownItem(label="最终补差", value=final_cost))

        return CostCalculationResult(
            brand=purchase.brand,
            new_gold_total=new_gold_total,
            labor_fee=labor_fee,
            old_weight=purchase.old_weight,
            loss_amount=loss_amount,
            exchangeable_weight=exchangeable_weight,
            recycle_price=recycle_price,
            old_gold_deduction=old_deduction,
            final_cost=final_cost,
            price_per_gram=price_per_gram,
            min_new_weight=min_new_weight,
            breakdown=breakdown,
            warnings=warnings,
        )

    def _calc_loss(self, old_weight: float, loss_type: str, loss_value: float) -> float:
        if old_weight <= 0:
            return 0.0
        if loss_type == "percentage":
            return round(old_weight * loss_value / 100, 4)
        return round(min(loss_value, old_weight), 4)

    def _loss_desc(self, rule: ExchangeRule | ExchangeRuleInline) -> str:
        if rule.loss_type == "percentage":
            return f"{rule.loss_value}%"
        return f"{rule.loss_value}g"

    def _resolve_recycle_price(
        self, purchase: PurchaseInfo, rule: ExchangeRule | ExchangeRuleInline
    ) -> float:
        if purchase.recycle_price is not None:
            return purchase.recycle_price
        if rule.recycle_price_type == "jewelry":
            return purchase.new_price
        return round(purchase.new_price * 0.85, 2)

    def _calc_labor(
        self, purchase: PurchaseInfo, rule: ExchangeRule | ExchangeRuleInline
    ) -> float:
        if purchase.labor_fee is not None:
            return round(purchase.labor_fee, 2)
        if rule.labor_type == "fixed":
            return round(rule.labor_value, 2)
        return round(rule.labor_value * purchase.new_weight, 2)
