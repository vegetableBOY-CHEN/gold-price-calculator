from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.gold_price import GoldPriceOverview, GoldPriceUpdate
from app.services.gold_price_service import GoldPriceService

router = APIRouter()


@router.get("", response_model=GoldPriceOverview)
async def get_prices(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """获取国内金价及品牌金价列表"""
    background_tasks.add_task(GoldPriceService.refresh_brand_prices_background)
    return GoldPriceService(db).get_overview()


@router.put("", response_model=GoldPriceOverview)
async def update_prices(data: GoldPriceUpdate, db: Session = Depends(get_db)):
    """手动更新金价（支持国内金价和品牌金价）"""
    return GoldPriceService(db).update_prices(data)
