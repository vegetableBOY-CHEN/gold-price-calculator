import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.db.models import BrandPrice, DomesticPrice, ExchangeRuleRecord
from app.main import app
from app.services.exchange_rule_service import DEFAULT_RULES
from app.services.gold_price_service import DEFAULT_BRANDS

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed(db):
    now = datetime.utcnow()
    db.add(DomesticPrice(price=960, updated_at=now))
    for brand_id, name, gold, bar in DEFAULT_BRANDS:
        db.add(BrandPrice(brand=brand_id, brand_name=name, gold_price=gold, bar_price=bar, updated_at=now))
    for item in DEFAULT_RULES:
        db.add(ExchangeRuleRecord(**item, created_at=now, updated_at=now))
    db.commit()


@pytest.fixture(autouse=True)
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestSession()
    _seed(db)
    db.close()

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
