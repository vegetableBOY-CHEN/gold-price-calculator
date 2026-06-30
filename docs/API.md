# API 文档

Base URL: `http://localhost:8000`

在线文档: `/docs` (Swagger UI) | `/redoc` (ReDoc)

## 健康检查

```
GET /health
```

**Response 200**

```json
{ "status": "ok", "service": "gold-price-calculator" }
```

---

## 品牌

### 获取品牌列表

```
GET /api/brands
```

**Response 200**

```json
[
  {
    "id": "chow_tai_fook",
    "name": "周大福",
    "name_en": "Chow Tai Fook",
    "description": "..."
  }
]
```

### 获取品牌详情

```
GET /api/brands/{brand_id}
```

**Response 200**: 完整 BrandRule 对象

**Response 404**: 品牌不存在

---

## 价格计算

### 计算价格

```
POST /api/calculate
Content-Type: application/json
```

**Request Body**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| brand_id | string | 是 | 品牌 ID |
| weight | float | 是 | 重量（克），> 0 |
| gold_price | float | 是 | 金价（元/克），> 0 |
| purity | float | 否 | 成色，默认 1.0 |
| extra_fees | float | 否 | 额外费用，默认 0 |

**Response 200**

```json
{
  "brand_id": "chow_tai_fook",
  "brand_name": "周大福",
  "weight": 10,
  "gold_price": 580,
  "purity": 0.999,
  "gold_value": 5794.2,
  "fees": [
    { "name": "工费", "amount": 500, "description": "按克计工费" }
  ],
  "extra_fees": 0,
  "total_price": 6294.2,
  "notes": "..."
}
```

**Response 400**: 参数错误或品牌不存在
