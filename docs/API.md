# API 文档

> 当前 API 版本：0.2.0
>
> 本地 Base URL：`http://localhost:8000`
>
> Swagger UI：`/docs`，ReDoc：`/redoc`

所有金额单位均为人民币元，重量单位为克，除非字段另有说明。

> 当前 API 没有登录鉴权。`PUT /api/prices` 和规则写接口会修改共享数据库，公网部署时必须通过反向代理、网络策略或后续用户系统限制访问。

## 1. 健康检查

### `GET /health`

响应：

```json
{
  "status": "ok",
  "service": "gold-price-calculator"
}
```

## 2. 金价概览

### `GET /api/prices`

返回 SQLite 中最近保存的大盘和品牌价格，并提交后台刷新任务。该请求不会同步等待外部行情源。

响应示例：

```json
{
  "domestic": {
    "price": 880,
    "update_time": "2026-08-03T13:00:00"
  },
  "international": [
    {
      "market": "international",
      "name": "国际现货黄金",
      "symbol": "GOLD",
      "exchange": null,
      "price": 2501,
      "currency": "USD",
      "unit": "oz",
      "change": 5,
      "change_percent": 0.2,
      "source": "AllTick",
      "status": "live",
      "update_time": "2026-08-03T13:00:00"
    }
  ],
  "domestic_markets": [
    {
      "market": "domestic",
      "name": "上海金 AU9999",
      "symbol": "AU9999",
      "exchange": "SGE",
      "price": 880,
      "currency": "CNY",
      "unit": "g",
      "change": 2,
      "change_percent": 0.3,
      "source": "Sina",
      "status": "cached",
      "update_time": "2026-08-03T13:00:00"
    }
  ],
  "brands": [
    {
      "brand": "chow_tai_fook",
      "brand_name": "周大福",
      "gold_price": 1231,
      "bar_price": 1090,
      "update_time": "2026-08-03T09:00:00"
    }
  ],
  "brand_refresh_interval_seconds": 28800,
  "market_refresh_interval_seconds": 5,
  "server_time": "2026-08-03T13:00:00+08:00"
}
```

`status` 含义：

| 值 | 含义 |
| --- | --- |
| `live` | 缓存更新时间距服务器当前时间不超过 30 秒 |
| `cached` | 有数据库记录，但不是最近 30 秒的数据 |
| `fallback` | 没有对应的大盘缓存，使用本地兜底值 |

### `PUT /api/prices`

手动更新国内价格和/或品牌价格。字段均可选。

```json
{
  "domestic_price": 880,
  "brands": [
    {
      "brand": "chow_tai_fook",
      "brand_name": "周大福",
      "gold_price": 1231,
      "bar_price": 1090
    }
  ]
}
```

响应为更新后的完整 `GoldPriceOverview`。

## 3. 门店规则

### `GET /api/rules`

获取全部规则。可使用查询参数按品牌过滤：

```text
GET /api/rules?brand=chow_tai_fook
```

### `GET /api/rules/{rule_id}`

获取单条规则。不存在时返回 `404`：

```json
{ "detail": "规则不存在" }
```

### `POST /api/rules`

创建规则，成功返回 `201`。

### `PUT /api/rules/{rule_id}`

完整更新规则。不存在时返回 `404`。

### `DELETE /api/rules/{rule_id}`

删除规则，成功返回 `204`，不存在时返回 `404`。

创建和更新使用相同结构：

```json
{
  "name": "周大福南京东路店",
  "brand": "chow_tai_fook",
  "store_name": "南京东路店",
  "city": "上海",
  "support_bar": true,
  "support_other_brand": true,
  "support_old_jewelry": true,
  "need_extra_gold": true,
  "extra_rate": 20,
  "loss_type": "percentage",
  "loss_value": 0.2,
  "labor_type": "perGram",
  "labor_value": 30,
  "recycle_price_type": "recycle"
}
```

字段约束：

| 字段 | 类型 | 约束或含义 |
| --- | --- | --- |
| `name` | string | 1～100 字符 |
| `brand` | string | 品牌 ID |
| `store_name` | string | 最长 100 字符，可为空 |
| `city` | string | 最长 100 字符，可为空 |
| `support_bar` | boolean | 是否支持金条置换 |
| `support_other_brand` | boolean | 是否支持跨品牌 |
| `support_old_jewelry` | boolean | 是否支持旧饰品 |
| `need_extra_gold` | boolean | 是否要求增金 |
| `extra_rate` | number | 百分比；要求增金时必须大于 0 |
| `loss_type` | string | 当前只允许 `percentage` |
| `loss_value` | number | 0～100，表示旧金每克损耗百分比 |
| `labor_type` | string | `fixed` 或 `perGram` |
| `labor_value` | number | 不小于 0 |
| `recycle_price_type` | string | `recycle` 或 `jewelry` |

规则响应还包含 `id`、`created_at` 和 `updated_at`。

## 4. 成本计算

### `POST /api/calculate`

可以通过 `rule_id` 使用数据库模板，也可以通过 `exchange_rule` 提交一次性规则。两者同时提供时，`exchange_rule` 优先。

使用模板：

```json
{
  "purchase": {
    "brand": "chow_tai_fook",
    "new_weight": 10,
    "new_price": 980,
    "labor_fee": 300,
    "old_weight": 8,
    "old_purchase_cost": 5000,
    "old_brand": "chow_sang_sang",
    "old_is_bar": false
  },
  "rule_id": 1
}
```

使用一次性规则：

```json
{
  "purchase": {
    "brand": "chow_tai_fook",
    "new_weight": 10,
    "new_price": 980,
    "labor_fee": 300,
    "old_weight": 8,
    "old_purchase_cost": 5000,
    "old_brand": "chow_sang_sang",
    "old_is_bar": false
  },
  "exchange_rule": {
    "support_bar": true,
    "support_other_brand": true,
    "support_old_jewelry": true,
    "need_extra_gold": true,
    "extra_rate": 20,
    "loss_type": "percentage",
    "loss_value": 0.2,
    "labor_type": "fixed",
    "labor_value": 0,
    "recycle_price_type": "recycle"
  }
}
```

`purchase` 字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `brand` | 是 | 新金品牌 ID |
| `new_weight` | 是 | 新金重量，必须大于 0 |
| `new_price` | 是 | 新金单价，必须大于 0 |
| `labor_fee` | 否 | 工费总额；提供时优先于规则工费 |
| `old_weight` | 否 | 旧金重量，默认 0 |
| `old_purchase_cost` | 否 | 旧金原购买成本，默认 0 |
| `old_brand` | 否 | 旧金品牌 |
| `old_is_bar` | 否 | 是否为金条，默认 `false` |
| `recycle_price` | 否 | 实际回收单价；当前前端不提供该输入 |

响应示例：

```json
{
  "brand": "chow_tai_fook",
  "new_gold_total": 9800,
  "labor_fee": 300,
  "old_weight": 8,
  "loss_amount": 0.016,
  "exchangeable_weight": 7.984,
  "recycle_price": 833,
  "old_gold_deduction": 6650.67,
  "direct_purchase_cost": 10100,
  "actual_cost": 8449.33,
  "savings_amount": 1650.67,
  "final_cost": 3449.33,
  "price_per_gram": 814.93,
  "min_new_weight": 9.6,
  "breakdown": [],
  "warnings": []
}
```

常见 `400` 错误：

- `该门店不支持金条置换`
- `该门店不支持跨品牌置换`
- `该门店不支持旧饰品置换`
- `增金比例不足：要求至少 ...`
- `规则模板 ID ... 不存在`

Pydantic 字段校验失败时返回 FastAPI 标准 `422` 响应。

## 5. 计算约定

```text
损耗重量 = 旧金重量 × loss_value ÷ 100
可抵扣重量 = 旧金重量 - 损耗重量
旧金抵扣 = 可抵扣重量 × 回收计价
需补差价 = 新金总价 + 工费 - 旧金抵扣
真实成本 = 旧金购买成本 + 需补差价
真实克均价 = (真实成本 - 工费) ÷ 新金重量
```

`recycle_price_type=recycle` 且未提供 `recycle_price` 时，当前计算引擎按 `new_price × 0.85` 估算。
