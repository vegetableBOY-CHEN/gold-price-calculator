# 数据库设计

## 当前状态 (v0.1)

**暂无数据库**。品牌规则以 JSON 文件存储，计算为无状态 API。

```
rules/brands/*.json  →  BrandService  →  PriceCalculator
```

## 未来规划 (v0.2+)

如需持久化，建议使用 SQLite（开发）/ PostgreSQL（生产）。

### 表设计草案

#### brands

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(50) PK | 品牌 ID |
| name | VARCHAR(100) | 中文名 |
| name_en | VARCHAR(100) | 英文名 |
| rules_json | JSONB | 完整规则 |
| updated_at | TIMESTAMP | 更新时间 |

#### calculation_history

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 记录 ID |
| brand_id | VARCHAR(50) FK | 品牌 |
| weight | DECIMAL | 重量 |
| gold_price | DECIMAL | 金价 |
| total_price | DECIMAL | 总价 |
| created_at | TIMESTAMP | 计算时间 |

#### gold_prices

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | |
| price | DECIMAL | 金价（元/克） |
| source | VARCHAR(50) | 数据来源 |
| fetched_at | TIMESTAMP | 获取时间 |

## 迁移策略

从 JSON 到数据库时：

1. 编写 seed 脚本读取 `rules/brands/*.json` 导入 `brands` 表
2. BrandService 改为从 DB 读取，保留 JSON 作为 fallback
3. 逐步添加历史记录与金价缓存功能
