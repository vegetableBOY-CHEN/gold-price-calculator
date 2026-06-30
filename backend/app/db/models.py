from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class DomesticPrice(Base):
    __tablename__ = "domestic_price"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    price: Mapped[float] = mapped_column(Float, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BrandPrice(Base):
    __tablename__ = "brand_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    brand_name: Mapped[str] = mapped_column(String(100))
    gold_price: Mapped[float] = mapped_column(Float, default=0)
    bar_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExchangeRuleRecord(Base):
    __tablename__ = "exchange_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    brand: Mapped[str] = mapped_column(String(50))
    support_bar: Mapped[bool] = mapped_column(Boolean, default=True)
    support_other_brand: Mapped[bool] = mapped_column(Boolean, default=True)
    support_old_jewelry: Mapped[bool] = mapped_column(Boolean, default=True)
    need_extra_gold: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_rate: Mapped[float] = mapped_column(Float, default=0)
    loss_type: Mapped[str] = mapped_column(String(20), default="fixed")
    loss_value: Mapped[float] = mapped_column(Float, default=0)
    labor_type: Mapped[str] = mapped_column(String(20), default="perGram")
    labor_value: Mapped[float] = mapped_column(Float, default=0)
    recycle_price_type: Mapped[str] = mapped_column(String(20), default="recycle")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
