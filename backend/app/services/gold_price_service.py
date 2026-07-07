import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
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
    ("lao_miao", "老庙黄金", 972, 952),
    ("lukfook", "六福珠宝", 978, 958),
]


@dataclass(frozen=True)
class MarketSymbol:
    symbol: str
    exchange: str
    name: str
    unit_label: str

    @property
    def currency(self) -> str:
        return self.unit_label.split("/", 1)[0] if "/" in self.unit_label else "CNY"

    @property
    def unit(self) -> str:
        return self.unit_label.split("/", 1)[1] if "/" in self.unit_label else self.unit_label


class AllTickQuoteClient:
    def __init__(self):
        self.settings = get_settings()

    def latest_prices(self, symbols: list[MarketSymbol]) -> dict[str, dict[str, Any]]:
        if not self.settings.alltick_token or not symbols:
            return {}

        payload = {
            "trace": f"gold-price-calculator-{int(datetime.utcnow().timestamp())}",
            "data": {
                "symbol_list": [
                    {"code": item.symbol, "exchange": item.exchange}
                    for item in symbols
                ]
            },
        }
        url = f"{self.settings.alltick_base_url.rstrip('/')}/quote-b-api/trade-tick"

        try:
            response = httpx.get(
                url,
                params={"token": self.settings.alltick_token, "query": json.dumps(payload)},
                timeout=self.settings.alltick_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return {}

        quotes: dict[str, dict[str, Any]] = {}
        for record in self._find_records(payload):
            code = str(record.get("code") or record.get("symbol") or record.get("s") or "")
            price = self._pick_number(record, ("last_price", "last", "price", "close", "c", "latest_price"))
            if not code or price is None:
                continue
            quotes[code.upper()] = {
                "price": price,
                "change": self._pick_number(record, ("change", "chg", "net_change")),
                "change_percent": self._pick_number(record, ("change_percent", "change_rate", "pct_chg", "percent")),
            }
        return quotes

    def _find_records(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []

        for key in ("tick_list", "list", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            nested = self._find_records(value)
            if nested:
                return nested
        return []

    def _pick_number(self, record: dict[str, Any], keys: tuple[str, ...]) -> float | None:
        for key in keys:
            value = record.get(key)
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None


class GoldPriceService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.quote_client = AllTickQuoteClient()

    def get_overview(self) -> GoldPriceOverview:
        now = datetime.utcnow()
        domestic = self.db.query(DomesticPrice).first()
        brands = self.db.query(BrandPrice).order_by(BrandPrice.id).all()
        international_symbols = self._parse_symbols(self.settings.alltick_international_symbols)
        domestic_symbols = self._parse_symbols(self.settings.alltick_domestic_symbols)
        quotes = self.quote_client.latest_prices(international_symbols + domestic_symbols)

        return GoldPriceOverview(
            domestic=DomesticGoldPrice(
                price=domestic.price if domestic else 0,
                update_time=domestic.updated_at if domestic else None,
            ),
            international=self._market_prices("international", international_symbols, quotes, now),
            domestic_markets=self._market_prices(
                "domestic",
                domestic_symbols,
                quotes,
                now,
                fallback_price=domestic.price if domestic else 0,
                fallback_time=domestic.updated_at if domestic else None,
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
            brand_refresh_interval_seconds=1800,
            market_refresh_interval_seconds=5,
            server_time=now,
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

    def _parse_symbols(self, raw: str) -> list[MarketSymbol]:
        symbols: list[MarketSymbol] = []
        for chunk in raw.split(","):
            parts = [part.strip() for part in chunk.split(":")]
            if len(parts) == 4 and parts[0]:
                symbols.append(MarketSymbol(parts[0], parts[1], parts[2], parts[3]))
        return symbols

    def _market_prices(
        self,
        market: str,
        symbols: list[MarketSymbol],
        quotes: dict[str, dict[str, Any]],
        now: datetime,
        fallback_price: float = 0,
        fallback_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        prices = []
        for item in symbols:
            quote = quotes.get(item.symbol.upper())
            prices.append(
                {
                    "market": market,
                    "name": item.name,
                    "symbol": item.symbol,
                    "exchange": item.exchange,
                    "price": quote["price"] if quote else fallback_price,
                    "currency": item.currency,
                    "unit": item.unit,
                    "change": quote.get("change") if quote else None,
                    "change_percent": quote.get("change_percent") if quote else None,
                    "source": "AllTick" if quote else "local",
                    "status": "live" if quote else "fallback",
                    "update_time": now if quote else fallback_time,
                }
            )
        return prices
