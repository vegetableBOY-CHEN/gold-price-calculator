from sqlalchemy.orm import Session

from app.calculator.exchange_engine import ExchangeCalculator
from app.models.purchase import CostCalculationRequest, CostCalculationResult
from app.services.exchange_rule_service import ExchangeRuleService


class CostCalculationService:
    def __init__(self, db: Session):
        self.db = db
        self.rule_service = ExchangeRuleService(db)
        self.calculator = ExchangeCalculator()

    def calculate(self, request: CostCalculationRequest) -> CostCalculationResult:
        rule = None
        if request.exchange_rule:
            rule = request.exchange_rule
        elif request.rule_id:
            rule = self.rule_service.get_rule(request.rule_id)
            if not rule:
                raise ValueError(f"规则模板 ID {request.rule_id} 不存在")
        else:
            from app.models.exchange_rule import ExchangeRuleCreate
            from app.models.purchase import ExchangeRuleInline

            rule = ExchangeRuleInline()

        return self.calculator.calculate(request.purchase, rule)
