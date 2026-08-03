import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_prices(client):
    response = await client.get("/api/prices")
    assert response.status_code == 200
    data = response.json()
    assert "domestic" in data
    assert "international" in data
    assert "domestic_markets" in data
    assert data["brand_refresh_interval_seconds"] == 28800
    assert data["market_refresh_interval_seconds"] == 5
    assert len(data["brands"]) >= 4


@pytest.mark.asyncio
async def test_list_rules(client):
    response = await client.get("/api/rules")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_calculate_cost(client):
    response = await client.post(
        "/api/calculate",
        json={
            "purchase": {
                "brand": "chow_tai_fook",
                "new_weight": 10,
                "new_price": 980,
                "old_weight": 8,
                "old_is_bar": False,
                "recycle_price": 850,
            },
            "rule_id": 1,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["final_cost"] > 0
    assert data["price_per_gram"] > 0


@pytest.mark.asyncio
async def test_crud_rule(client):
    create_resp = await client.post(
        "/api/rules",
        json={
            "name": "测试规则",
            "brand": "china_gold",
            "store_name": "测试商场店",
            "city": "上海",
            "support_bar": True,
            "support_other_brand": True,
            "support_old_jewelry": True,
            "need_extra_gold": False,
            "extra_rate": 0,
            "loss_type": "percentage",
            "loss_value": 0.1,
            "labor_type": "perGram",
            "labor_value": 20,
            "recycle_price_type": "recycle",
        },
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["store_name"] == "测试商场店"
    assert create_resp.json()["city"] == "上海"
    rule_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/rules/{rule_id}")
    assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_calculate_rejects_insufficient_extra_gold(client):
    response = await client.post(
        "/api/calculate",
        json={
            "purchase": {
                "brand": "chow_tai_fook",
                "new_weight": 8,
                "new_price": 980,
                "old_weight": 8,
                "old_is_bar": False,
                "recycle_price": 850,
            },
            "rule_id": 1,
        },
    )

    assert response.status_code == 400
    assert "增金比例不足" in response.json()["detail"]
