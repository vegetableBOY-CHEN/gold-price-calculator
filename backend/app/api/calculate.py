from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.purchase import CostCalculationRequest, CostCalculationResult
from app.services.cost_calculation_service import CostCalculationService

router = APIRouter()


@router.post("", response_model=CostCalculationResult)
async def calculate_cost(request: CostCalculationRequest, db: Session = Depends(get_db)):
    """计算金饰购买成本（含旧金置换）"""
    try:
        return CostCalculationService(db).calculate(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
