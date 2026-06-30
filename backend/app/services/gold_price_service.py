from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import BrandPrice, DomesticPrice
from app.models.gold_price import (
    DomesticGoldPrice,
    GoldPriceItem,
    GoldPriceOverview,
    GoldPriceUpdate,
)

DEFAULT_BRANDS = [
    ("chow_tai_fook", "周大福", 980, 960),
    ("chow_sang_sang", "周生生", 975, 955),
    ("lao_feng_xiang", "老凤祥", 970, 950),
    ("china_gold", "中国黄金", 965, 945),
]


class GoldPriceService:
    def __init__(self, db: Session):
        self.db = db

    def get_overview(self) -> GoldPriceOverview:
        domestic = self.db.query(DomesticPrice).first()
        brands = self.db.query(BrandPrice).order_by(BrandPrice.id).all()

        return GoldPriceOverview(
            domestic=DomesticGoldPrice(
                price=domestic.price if domestic else 0,
                update_time=domestic.updated_at if domestic else None,
            ),
            brands=[
                GoldPriceItem(
                    brand=b.brand,
                    brand_name=b.brand_name,
                    gold_price=b.gold_price,
                    bar_price=b.bar_price,
                    update_time=b.updated_at,
                )
                for b in brands
            ],
        )

    def update_prices(self, data: GoldPriceUpdate) -> GoldPriceOverview:
        now = datetime.utcnow()

        if data.domestic_price is not None:
            domestic = self.db.query(DomesticPrice).first()
            if not domestic:
                domestic = DomesticPrice(price=data.domestic_price, updated_at=now)
                self.db.add(domestic)
            else:
                domestic.price = data.domestic_price
                domestic.updated_at = now

        if data.brands:
            for item in data.brands:
                record = self.db.query(BrandPrice).filter_by(brand=item.brand).first()
                if record:
                    record.gold_price = item.gold_price
                    record.bar_price = item.bar_price
                    record.brand_name = item.brand_name
                    record.updated_at = now
                else:
                    self.db.add(
                        BrandPrice(
                            brand=item.brand,
                            brand_name=item.brand_name,
                            gold_price=item.gold_price,
                            bar_price=item.bar_price,
                            updated_at=now,
                        )
                    )

        self.db.commit()
        return self.get_overview()

    def seed_if_empty(self):
        if self.db.query(DomesticPrice).first() is None:
            self.db.add(DomesticPrice(price=960, updated_at=datetime.utcnow()))

        if self.db.query(BrandPrice).count() == 0:
            now = datetime.utcnow()
            for brand_id, name, gold, bar in DEFAULT_BRANDS:
                self.db.add(
                    BrandPrice(
                        brand=brand_id,
                        brand_name=name,
                        gold_price=gold,
                        bar_price=bar,
                        updated_at=now,
                    )
                )
        self.db.commit()
