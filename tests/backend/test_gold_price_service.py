from datetime import datetime

from app.db.models import BrandPrice, MarketPriceRecord
from app.services.gold_price_service import BrandPriceSnapshot, GoldPriceService


class FailingBrandClient:
    brand = "chow_tai_fook"

    def latest_price(self):
        raise RuntimeError("品牌来源暂不可用")


class WorkingBrandClient:
    brand = "chow_sang_sang"

    def latest_price(self):
        return BrandPriceSnapshot(
            brand=self.brand,
            brand_name="周生生",
            gold_price=1225,
            bar_price=1075,
            update_time=datetime(2026, 8, 1, 9, 30),
        )


def test_brand_refresh_continues_after_one_source_fails(db_session):
    service = GoldPriceService(db_session)
    service.brand_price_clients = [FailingBrandClient(), WorkingBrandClient()]

    service.refresh_brand_prices(datetime(2026, 8, 1, 12, 0))

    updated = db_session.query(BrandPrice).filter_by(brand="chow_sang_sang").one()
    assert updated.gold_price == 1225
    assert updated.bar_price == 1075
    assert updated.updated_at == datetime(2026, 8, 1, 9, 30)


class UnexpectedMarketClient:
    def latest_prices(self, _symbols):
        raise AssertionError("读取行情概览时不应同步访问外部行情源")


class UnexpectedDomesticClient:
    def latest_domestic_prices(self, _symbols):
        raise AssertionError("读取行情概览时不应同步访问国内行情源")


def test_overview_reads_market_cache_without_external_requests(db_session):
    db_session.add(
        MarketPriceRecord(
            market="international",
            name="国际现货黄金",
            symbol="GOLD",
            exchange=None,
            price=2500,
            currency="USD",
            unit="oz",
            source="cached-test",
            updated_at=datetime(2026, 8, 3, 12, 0),
        )
    )
    db_session.commit()
    service = GoldPriceService(db_session)
    service.quote_client = UnexpectedMarketClient()
    service.domestic_quote_client = UnexpectedDomesticClient()

    result = service.get_overview()

    assert result.international[0].price == 2500
    assert result.international[0].source == "cached-test"


class WorkingMarketClient:
    def latest_prices(self, symbols):
        return {
            item.symbol.upper(): {
                "price": 2501,
                "change": 5,
                "change_percent": 0.2,
                "source": "market-test",
                "update_time": datetime(2026, 8, 3, 13, 0),
            }
            for item in symbols
            if item.symbol.upper() == "GOLD"
        }


class WorkingDomesticClient:
    def latest_domestic_prices(self, symbols):
        return {
            "AU9999": {
                "price": 880,
                "change": 2,
                "change_percent": 0.3,
                "source": "domestic-test",
                "update_time": datetime(2026, 8, 3, 13, 0),
            }
        }


def test_market_refresh_persists_quotes_for_fast_reads(db_session):
    service = GoldPriceService(db_session)
    service.quote_client = WorkingMarketClient()
    service.domestic_quote_client = WorkingDomesticClient()

    service.refresh_market_prices()

    records = db_session.query(MarketPriceRecord).all()
    assert {(record.market, record.symbol) for record in records} == {
        ("international", "GOLD"),
        ("domestic", "AU9999"),
    }
    assert next(record for record in records if record.symbol == "AU9999").price == 880
