import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html import unescape
from datetime import datetime, timezone, timedelta
from typing import Any
import re
import threading
import time

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import BrandPrice, DomesticPrice, MarketPriceRecord
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
    ("lao_miao", "老庙黄金", 972, 952),
    ("lukfook", "六福珠宝", 978, 958),
    ("zhou_da_sheng", "周大生", 965, 945),
    ("jin_zhi_zun", "金至尊", 970, 950),
]
VISIBLE_BRANDS = {brand_id for brand_id, _, _, _ in DEFAULT_BRANDS}
BEIJING_TZ = timezone(timedelta(hours=8))
BRAND_REFRESH_INTERVAL_SECONDS = 8 * 60 * 60
MARKET_TIMEOUT_SECONDS = 3
BRAND_TIMEOUT_SECONDS = 3


def beijing_now() -> datetime:
    return datetime.now(BEIJING_TZ)


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


@dataclass(frozen=True)
class BrandPriceSnapshot:
    brand: str
    brand_name: str
    gold_price: float
    bar_price: float | None
    update_time: datetime


class AllTickQuoteClient:
    _last_quotes: dict[str, dict[str, Any]] = {}

    def __init__(self):
        self.settings = get_settings()

    def latest_prices(self, symbols: list[MarketSymbol]) -> dict[str, dict[str, Any]]:
        if not self.settings.alltick_token or not symbols:
            return {}

        payload = {
            "trace": f"gold-price-calculator-{int(beijing_now().timestamp())}",
            "data": {
                "symbol_list": [self._symbol_payload(item) for item in symbols],
            },
        }
        url = f"{self.settings.alltick_base_url.rstrip('/')}/quote-b-api/trade-tick"

        try:
            response = httpx.get(
                url,
                params={"token": self.settings.alltick_token, "query": json.dumps(payload)},
                timeout=min(self.settings.alltick_timeout_seconds, MARKET_TIMEOUT_SECONDS),
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
                "source": "AllTick",
                "update_time": beijing_now(),
            }
        self._last_quotes.update(quotes)
        return quotes

    def _symbol_payload(self, symbol: MarketSymbol) -> dict[str, str]:
        payload = {"code": symbol.symbol}
        if symbol.exchange:
            payload["exchange"] = symbol.exchange
        return payload

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


class SinaGoldQuoteClient:
    def latest_domestic_prices(self, symbols: list[MarketSymbol]) -> dict[str, dict[str, Any]]:
        if not any(item.symbol.upper() == "AU9999" for item in symbols):
            return {}

        try:
            response = httpx.get(
                "https://hq.sinajs.cn/list=gds_AU9999",
                headers={"Referer": "https://finance.sina.com.cn"},
                timeout=MARKET_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return {}

        text = response.text
        if '"' not in text:
            return {}
        fields = text.split('"', 2)[1].split(",")
        if len(fields) < 14 or not fields[0]:
            return {}

        try:
            price = float(fields[0])
            previous_close = float(fields[7]) if fields[7] else None
        except ValueError:
            return {}

        change = price - previous_close if previous_close else None
        change_percent = change / previous_close * 100 if change is not None and previous_close else None
        update_time = self._parse_datetime(fields[12], fields[6])
        return {
            "AU9999": {
                "price": price,
                "change": change,
                "change_percent": change_percent,
                "source": "Sina",
                "update_time": update_time,
            }
        }

    def _parse_datetime(self, date_value: str, time_value: str) -> datetime:
        try:
            return datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=BEIJING_TZ)
        except ValueError:
            return beijing_now()


class ChowTaiFookGoldPriceClient:
    brand = "chow_tai_fook"
    brand_name = "周大福"

    def latest_price(self) -> BrandPriceSnapshot | None:
        try:
            response = httpx.get(
                "https://api2.ctfmall.com/gateway/ctfmall-common2-server/common/ctfTodayGoldPriceNew",
                headers={"appId": "ctfmall-web", "Referer": "https://www.ctfmall.com/todaygold"},
                timeout=BRAND_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            response.encoding = "utf-8"
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return None

        data = payload.get("data") if isinstance(payload, dict) else None
        categories = data.get("goldPriceDailyListVO", []) if isinstance(data, dict) else []
        items = [
            item
            for category in categories
            for item in category.get("goldPriceInfoListVO", [])
            if isinstance(item, dict) and item.get("isEnabled") and item.get("isShowInFrontend")
        ]
        jewelry_price = self._find_price(items, sort_order=1, preferred_names=("足金",))
        bar_price = self._find_price(items, sort_order=2, preferred_names=("金条", "黄金"))
        if jewelry_price is None:
            return None

        return BrandPriceSnapshot(self.brand, self.brand_name, jewelry_price, bar_price, beijing_now().replace(tzinfo=None))

    def _find_price(
        self,
        items: list[dict[str, Any]],
        sort_order: int,
        preferred_names: tuple[str, ...],
    ) -> float | None:
        matched = [
            item
            for item in items
            if item.get("sortOrder") == sort_order
            or any(name in str(item.get("displayName", "")) or name in str(item.get("originalName", "")) for name in preferred_names)
        ]
        if not matched:
            return None
        try:
            return float(matched[0]["goldPrice"])
        except (KeyError, TypeError, ValueError):
            return None


class ChowSangSangGoldPriceClient:
    brand = "chow_sang_sang"
    brand_name = "周生生"

    def latest_price(self) -> BrandPriceSnapshot | None:
        try:
            response = httpx.get(
                "https://cn.chowsangsang.com/gold-info",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=BRAND_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        match = re.search(r":gold_data='([^']+)'", response.text)
        if not match:
            return None

        try:
            records = json.loads(unescape(match.group(1)))
        except ValueError:
            return None

        by_type = {str(item.get("type")): item for item in records if isinstance(item, dict)}
        jewelry_price = self._price_from_record(by_type.get("G_JW_SELL"))
        bar_price = self._price_from_record(by_type.get("G_INGOT_SELL"))
        if jewelry_price is None:
            return None

        update_time = self._parse_update_time(by_type.get("G_JW_SELL"))
        return BrandPriceSnapshot(self.brand, self.brand_name, jewelry_price, bar_price, update_time)

    def _price_from_record(self, record: dict[str, Any] | None) -> float | None:
        if not record:
            return None
        try:
            return float(record["price"])
        except (KeyError, TypeError, ValueError):
            return None

    def _parse_update_time(self, record: dict[str, Any] | None) -> datetime:
        value = record.get("lastUpdateDate") if record else None
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).astimezone(BEIJING_TZ).replace(tzinfo=None)
            except ValueError:
                pass
        return beijing_now().replace(tzinfo=None)


class LukfookGoldPriceClient:
    brand = "lukfook"
    brand_name = "六福珠宝"

    def latest_price(self) -> BrandPriceSnapshot | None:
        try:
            response = httpx.get(
                "https://www.lukfook.com/api/goldprice/page",
                headers={"Referer": "https://www.lukfook.com/tc/page/goldprice", "User-Agent": "Mozilla/5.0"},
                timeout=BRAND_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return None

        data = payload.get("data") if isinstance(payload, dict) else None
        group = data.get("group", []) if isinstance(data, dict) else []
        try:
            jewelry_price = float(group[0]["GoldS"])
            bar_price = float(group[2]["InvestmentS"])
        except (IndexError, KeyError, TypeError, ValueError):
            return None

        update_time = self._parse_record_date(data.get("record_date") if isinstance(data, dict) else None)
        return BrandPriceSnapshot(self.brand, self.brand_name, jewelry_price, bar_price, update_time)

    def _parse_record_date(self, value: Any) -> datetime:
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        return beijing_now().replace(tzinfo=None)


class CnGoldBrandPriceClient:
    def __init__(self, brand: str, brand_name: str, page_slug: str, jewelry_code: str, bar_code: str | None):
        self.brand = brand
        self.brand_name = brand_name
        self.page_slug = page_slug
        self.jewelry_code = jewelry_code
        self.bar_code = bar_code

    def latest_price(self) -> BrandPriceSnapshot | None:
        codes = [self.jewelry_code]
        if self.bar_code:
            codes.append(self.bar_code)

        try:
            response = httpx.get(
                "https://api.jijinhao.com/quoteCenter/realTime.htm",
                params={"codes": ",".join(codes) + ","},
                headers={
                    "Referer": f"https://quote.cngold.org/gjs/{self.page_slug}.html",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
                timeout=BRAND_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        payload = self._parse_jsonp(response.text)
        if not payload:
            return None

        jewelry = payload.get(self.jewelry_code)
        bar = payload.get(self.bar_code) if self.bar_code else None
        jewelry_price = self._quote_price(jewelry)
        if jewelry_price is None:
            return None

        return BrandPriceSnapshot(
            self.brand,
            self.brand_name,
            jewelry_price,
            self._quote_price(bar),
            self._quote_time(jewelry),
        )

    def _parse_jsonp(self, text: str) -> dict[str, Any] | None:
        match = re.search(r"quote_json\s*=\s*(\{.*\})\s*;?\s*$", text.strip(), re.S)
        if not match:
            return None
        try:
            payload = json.loads(match.group(1))
        except ValueError:
            return None
        return payload if isinstance(payload, dict) else None

    def _quote_price(self, quote: Any) -> float | None:
        if not isinstance(quote, dict):
            return None
        for key in ("q63", "q1", "q4"):
            value = quote.get(key)
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None

    def _quote_time(self, quote: Any) -> datetime:
        if isinstance(quote, dict):
            try:
                return datetime.fromtimestamp(float(quote["time"]) / 1000, BEIJING_TZ).replace(tzinfo=None)
            except (KeyError, TypeError, ValueError, OSError):
                pass
        return beijing_now().replace(tzinfo=None)


class GoldPriceService:
    _brand_refresh_lock = threading.Lock()
    _market_refresh_lock = threading.Lock()
    _last_market_refresh_attempt = 0.0

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.quote_client = AllTickQuoteClient()
        self.domestic_quote_client = SinaGoldQuoteClient()
        self.brand_price_clients = [
            ChowTaiFookGoldPriceClient(),
            ChowSangSangGoldPriceClient(),
            CnGoldBrandPriceClient("lao_feng_xiang", "老凤祥", "swhj_lfx", "JO_42659", "JO_351184"),
            LukfookGoldPriceClient(),
            CnGoldBrandPriceClient("zhou_da_sheng", "周大生", "swhj_zds", "JO_52678", "JO_351256"),
            CnGoldBrandPriceClient("lao_miao", "老庙黄金", "swhj_lm", "JO_42636", "JO_42637"),
            CnGoldBrandPriceClient("jin_zhi_zun", "金至尊", "swhj_jzz", "JO_42668", "JO_351253"),
        ]

    def get_overview(self) -> GoldPriceOverview:
        now = beijing_now()
        domestic = self.db.query(DomesticPrice).first()
        brands = self.db.query(BrandPrice).filter(BrandPrice.brand.in_(VISIBLE_BRANDS)).order_by(BrandPrice.id).all()
        international_symbols = self._parse_symbols(self.settings.alltick_international_symbols)
        domestic_symbols = self._parse_symbols(self.settings.alltick_domestic_symbols)
        cached_market_prices = {
            (record.market, record.symbol.upper()): record
            for record in self.db.query(MarketPriceRecord).all()
        }

        return GoldPriceOverview(
            domestic=DomesticGoldPrice(
                price=domestic.price if domestic else 0,
                update_time=domestic.updated_at if domestic else None,
            ),
            international=self._market_prices(
                "international", international_symbols, cached_market_prices, now
            ),
            domestic_markets=self._market_prices(
                "domestic",
                domestic_symbols,
                cached_market_prices,
                now,
                fallback_price=domestic.price if domestic else 0,
                fallback_time=domestic.updated_at if domestic else None,
            ),
            brands=[
                GoldPriceItem(
                    brand=brand.brand,
                    brand_name=brand.brand_name,
                    gold_price=brand.gold_price,
                    bar_price=brand.bar_price,
                    update_time=brand.updated_at,
                )
                for brand in brands
            ],
            brand_refresh_interval_seconds=BRAND_REFRESH_INTERVAL_SECONDS,
            market_refresh_interval_seconds=5,
            server_time=now,
        )

    @classmethod
    def refresh_market_prices_background(cls):
        if not cls._market_refresh_lock.acquire(blocking=False):
            return

        try:
            current_attempt = time.monotonic()
            if current_attempt - cls._last_market_refresh_attempt < 5:
                return
            cls._last_market_refresh_attempt = current_attempt

            from app.db.database import SessionLocal

            db = SessionLocal()
            try:
                cls(db).refresh_market_prices()
            finally:
                db.close()
        finally:
            cls._market_refresh_lock.release()

    def refresh_market_prices(self):
        international_symbols = self._parse_symbols(self.settings.alltick_international_symbols)
        domestic_symbols = self._parse_symbols(self.settings.alltick_domestic_symbols)
        all_symbols = international_symbols + domestic_symbols
        quotes = self.quote_client.latest_prices(all_symbols)
        quotes.update(
            {
                symbol: quote
                for symbol, quote in self.domestic_quote_client.latest_domestic_prices(domestic_symbols).items()
                if symbol not in quotes
            }
        )
        if not quotes:
            return

        now = beijing_now().replace(tzinfo=None)
        for market, symbols in (
            ("international", international_symbols),
            ("domestic", domestic_symbols),
        ):
            for item in symbols:
                quote = quotes.get(item.symbol.upper())
                if not quote:
                    continue
                record = (
                    self.db.query(MarketPriceRecord)
                    .filter_by(market=market, symbol=item.symbol)
                    .first()
                )
                update_time = quote.get("update_time") or now
                if isinstance(update_time, datetime) and update_time.tzinfo is not None:
                    update_time = update_time.astimezone(BEIJING_TZ).replace(tzinfo=None)
                values = {
                    "name": item.name,
                    "exchange": item.exchange or None,
                    "price": float(quote["price"]),
                    "currency": item.currency,
                    "unit": item.unit,
                    "change": quote.get("change"),
                    "change_percent": quote.get("change_percent"),
                    "source": quote.get("source", "local"),
                    "updated_at": update_time,
                }
                if record:
                    for key, value in values.items():
                        setattr(record, key, value)
                else:
                    self.db.add(
                        MarketPriceRecord(
                            market=market,
                            symbol=item.symbol,
                            **values,
                        )
                    )

                if market == "domestic" and item.symbol.upper() == "AU9999":
                    domestic = self.db.query(DomesticPrice).first()
                    if domestic:
                        domestic.price = float(quote["price"])
                        domestic.updated_at = update_time
                    else:
                        self.db.add(
                            DomesticPrice(price=float(quote["price"]), updated_at=update_time)
                        )
        self.db.commit()

    @classmethod
    def refresh_brand_prices_background(cls):
        if not cls._brand_refresh_lock.acquire(blocking=False):
            return

        from app.db.database import SessionLocal

        db = SessionLocal()
        try:
            # 一次刷新所有过期品牌，避免某个失败的来源长期挡住后续品牌。
            cls(db).refresh_brand_prices(beijing_now().replace(tzinfo=None))
        finally:
            db.close()
            cls._brand_refresh_lock.release()

    def refresh_brand_prices(self, now: datetime, max_clients: int | None = None):
        clients_to_refresh = []
        for client in self.brand_price_clients:
            record = self.db.query(BrandPrice).filter_by(brand=client.brand).first()
            if (
                record
                and record.updated_at
                and not self._is_default_brand_price(record)
                and (now - record.updated_at).total_seconds() < BRAND_REFRESH_INTERVAL_SECONDS
            ):
                continue

            if max_clients is not None and len(clients_to_refresh) >= max_clients:
                break
            clients_to_refresh.append(client)

        if not clients_to_refresh:
            return

        # 品牌来源互不依赖，并行请求可让首页在下一轮轮询时拿到整批新价。
        with ThreadPoolExecutor(max_workers=min(4, len(clients_to_refresh))) as executor:
            futures = {executor.submit(client.latest_price): client for client in clients_to_refresh}
            for future in as_completed(futures):
                try:
                    price = future.result()
                except Exception:
                    # 单个品牌源异常不应中断其他品牌的更新。
                    continue
                if not price:
                    continue

                record = self.db.query(BrandPrice).filter_by(brand=price.brand).first()
                if record:
                    record.brand_name = price.brand_name
                    record.gold_price = price.gold_price
                    record.bar_price = price.bar_price
                    record.updated_at = price.update_time
                else:
                    self.db.add(
                        BrandPrice(
                            brand=price.brand,
                            brand_name=price.brand_name,
                            gold_price=price.gold_price,
                            bar_price=price.bar_price,
                            updated_at=price.update_time,
                        )
                    )
                # 逐个提交，已返回的品牌无需等待最慢的来源。
                self.db.commit()

    def _is_default_brand_price(self, record: BrandPrice) -> bool:
        for brand_id, _, gold, bar in DEFAULT_BRANDS:
            if record.brand == brand_id and record.gold_price == gold and record.bar_price == bar:
                return True
        return False

    def update_prices(self, data: GoldPriceUpdate) -> GoldPriceOverview:
        now = beijing_now()

        if data.domestic_price is not None:
            domestic = self.db.query(DomesticPrice).first()
            if not domestic:
                domestic = DomesticPrice(price=data.domestic_price, updated_at=now.replace(tzinfo=None))
                self.db.add(domestic)
            else:
                domestic.price = data.domestic_price
                domestic.updated_at = now.replace(tzinfo=None)

        if data.brands:
            for item in data.brands:
                record = self.db.query(BrandPrice).filter_by(brand=item.brand).first()
                if record:
                    record.gold_price = item.gold_price
                    record.bar_price = item.bar_price
                    record.brand_name = item.brand_name
                    record.updated_at = now.replace(tzinfo=None)
                else:
                    self.db.add(
                        BrandPrice(
                            brand=item.brand,
                            brand_name=item.brand_name,
                            gold_price=item.gold_price,
                            bar_price=item.bar_price,
                            updated_at=now.replace(tzinfo=None),
                        )
                    )

        self.db.commit()
        return self.get_overview()

    def seed_if_empty(self):
        if self.db.query(DomesticPrice).first() is None:
            self.db.add(DomesticPrice(price=960, updated_at=beijing_now().replace(tzinfo=None)))

        now = beijing_now().replace(tzinfo=None)
        for brand_id, name, gold, bar in DEFAULT_BRANDS:
            if self.db.query(BrandPrice).filter_by(brand=brand_id).first() is None:
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
        cached_prices: dict[tuple[str, str], MarketPriceRecord],
        now: datetime,
        fallback_price: float = 0,
        fallback_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        prices = []
        for item in symbols:
            record = cached_prices.get((market, item.symbol.upper()))
            age_seconds = None
            if record and record.updated_at:
                age_seconds = (now.replace(tzinfo=None) - record.updated_at).total_seconds()
            prices.append(
                {
                    "market": market,
                    "name": item.name,
                    "symbol": item.symbol,
                    "exchange": item.exchange or None,
                    "price": record.price if record else fallback_price,
                    "currency": item.currency,
                    "unit": item.unit,
                    "change": record.change if record else None,
                    "change_percent": record.change_percent if record else None,
                    "source": record.source if record else "local",
                    "status": "live" if age_seconds is not None and age_seconds <= 30 else "cached" if record else "fallback",
                    "update_time": record.updated_at if record else fallback_time,
                }
            )
        return prices
