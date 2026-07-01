import pytest
from app.calculator.exchange_engine import ExchangeCalculator
from app.models.exchange_rule import ExchangeRule
from app.models.purchase import PurchaseInfo


@pytest.fixture
def calculator():
    return ExchangeCalculator()


@pytest.fixture
def default_rule():
    return ExchangeRule(
        name="测试",
        brand="chow_tai_fook",
        need_extra_gold=True,
        extra_rate=20,
        loss_type="fixed",
        loss_value=0.2,
        labor_type="perGram",
        labor_value=30,
        recycle_price_type="recycle",
    )


def test_new_gold_only(calculator, default_rule):
    purchase = PurchaseInfo(
        brand="chow_tai_fook",
        new_weight=10,
        new_price=980,
        old_weight=0,
        old_is_bar=False,
    )
    result = calculator.calculate(purchase, default_rule)

    assert result.new_gold_total == 9800
    assert result.labor_fee == 300
    assert result.old_gold_deduction == 0
    assert result.direct_purchase_cost == 10100
    assert result.actual_cost == 10100
    assert result.savings_amount == 0
    assert result.final_cost == 10100
    assert result.price_per_gram == 980


def test_exchange_with_old_gold(calculator, default_rule):
    purchase = PurchaseInfo(
        brand="chow_tai_fook",
        new_weight=10,
        new_price=980,
        old_weight=8,
        old_purchase_cost=6000,
        old_is_bar=False,
        recycle_price=850,
    )
    result = calculator.calculate(purchase, default_rule)

    assert result.loss_amount == 0.2
    assert result.exchangeable_weight == 7.8
    assert result.old_gold_deduction == 6630
    assert result.direct_purchase_cost == 10100
    assert result.final_cost == 3470
    assert result.actual_cost == 9470
    assert result.savings_amount == 630
    assert result.price_per_gram == 917


def test_extra_gold_warning(calculator, default_rule):
    purchase = PurchaseInfo(
        brand="chow_tai_fook",
        new_weight=8,
        new_price=980,
        old_weight=8,
        old_is_bar=False,
        recycle_price=850,
    )
    result = calculator.calculate(purchase, default_rule)

    assert result.min_new_weight == 9.6
    assert any("增金" in w for w in result.warnings)


def test_unsupported_bar(calculator, default_rule):
    default_rule.support_bar = False
    purchase = PurchaseInfo(
        brand="chow_tai_fook",
        new_weight=10,
        new_price=980,
        old_weight=5,
        old_is_bar=True,
    )
    with pytest.raises(ValueError, match="金条"):
        calculator.calculate(purchase, default_rule)
