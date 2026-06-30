from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import ExchangeRuleRecord
from app.models.exchange_rule import ExchangeRule, ExchangeRuleCreate

DEFAULT_RULES = [
    {
        "name": "周大福默认规则",
        "brand": "chow_tai_fook",
        "support_bar": True,
        "support_other_brand": True,
        "support_old_jewelry": True,
        "need_extra_gold": True,
        "extra_rate": 20,
        "loss_type": "fixed",
        "loss_value": 0.2,
        "labor_type": "perGram",
        "labor_value": 30,
        "recycle_price_type": "recycle",
    },
    {
        "name": "周生生默认规则",
        "brand": "chow_sang_sang",
        "support_bar": False,
        "support_other_brand": True,
        "support_old_jewelry": True,
        "need_extra_gold": True,
        "extra_rate": 15,
        "loss_type": "fixed",
        "loss_value": 0.15,
        "labor_type": "perGram",
        "labor_value": 28,
        "recycle_price_type": "recycle",
    },
    {
        "name": "老凤祥默认规则",
        "brand": "lao_feng_xiang",
        "support_bar": True,
        "support_other_brand": False,
        "support_old_jewelry": True,
        "need_extra_gold": False,
        "extra_rate": 0,
        "loss_type": "percentage",
        "loss_value": 2,
        "labor_type": "perGram",
        "labor_value": 25,
        "recycle_price_type": "jewelry",
    },
]


class ExchangeRuleService:
    def __init__(self, db: Session):
        self.db = db

    def _to_schema(self, record: ExchangeRuleRecord) -> ExchangeRule:
        return ExchangeRule(
            id=record.id,
            name=record.name,
            brand=record.brand,
            support_bar=record.support_bar,
            support_other_brand=record.support_other_brand,
            support_old_jewelry=record.support_old_jewelry,
            need_extra_gold=record.need_extra_gold,
            extra_rate=record.extra_rate,
            loss_type=record.loss_type,
            loss_value=record.loss_value,
            labor_type=record.labor_type,
            labor_value=record.labor_value,
            recycle_price_type=record.recycle_price_type,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def list_rules(self, brand: str | None = None) -> list[ExchangeRule]:
        query = self.db.query(ExchangeRuleRecord)
        if brand:
            query = query.filter_by(brand=brand)
        return [self._to_schema(r) for r in query.order_by(ExchangeRuleRecord.id).all()]

    def get_rule(self, rule_id: int) -> ExchangeRule | None:
        record = self.db.query(ExchangeRuleRecord).filter_by(id=rule_id).first()
        return self._to_schema(record) if record else None

    def create_rule(self, data: ExchangeRuleCreate) -> ExchangeRule:
        now = datetime.utcnow()
        record = ExchangeRuleRecord(**data.model_dump(), created_at=now, updated_at=now)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return self._to_schema(record)

    def update_rule(self, rule_id: int, data: ExchangeRuleCreate) -> ExchangeRule | None:
        record = self.db.query(ExchangeRuleRecord).filter_by(id=rule_id).first()
        if not record:
            return None
        for key, value in data.model_dump().items():
            setattr(record, key, value)
        record.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(record)
        return self._to_schema(record)

    def delete_rule(self, rule_id: int) -> bool:
        record = self.db.query(ExchangeRuleRecord).filter_by(id=rule_id).first()
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True

    def seed_if_empty(self):
        if self.db.query(ExchangeRuleRecord).count() > 0:
            return
        now = datetime.utcnow()
        for item in DEFAULT_RULES:
            self.db.add(ExchangeRuleRecord(**item, created_at=now, updated_at=now))
        self.db.commit()
