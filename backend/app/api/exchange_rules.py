from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.exchange_rule import ExchangeRule, ExchangeRuleCreate
from app.services.exchange_rule_service import ExchangeRuleService

router = APIRouter()


@router.get("", response_model=list[ExchangeRule])
async def list_rules(brand: str | None = None, db: Session = Depends(get_db)):
    """获取门店置换规则模板列表"""
    return ExchangeRuleService(db).list_rules(brand)


@router.get("/{rule_id}", response_model=ExchangeRule)
async def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = ExchangeRuleService(db).get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return rule


@router.post("", response_model=ExchangeRule, status_code=201)
async def create_rule(data: ExchangeRuleCreate, db: Session = Depends(get_db)):
    """新建门店规则模板"""
    return ExchangeRuleService(db).create_rule(data)


@router.put("/{rule_id}", response_model=ExchangeRule)
async def update_rule(rule_id: int, data: ExchangeRuleCreate, db: Session = Depends(get_db)):
    rule = ExchangeRuleService(db).update_rule(rule_id, data)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return rule


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    if not ExchangeRuleService(db).delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="规则不存在")
