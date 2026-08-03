# 数据库设计

> 当前状态：已使用 SQLite 持久化价格缓存和门店规则。默认文件为 `data/gold.db`。

## 1. 运行方式

后端启动时会：

1. 根据 `DATABASE_URL` 创建 SQLAlchemy Engine。
2. 自动创建缺失的数据表。
3. 为早期数据库的 `exchange_rules` 表补充 `city` 和 `store_name` 字段。
4. 数据为空时写入国内价、品牌价和默认规则种子数据。

默认连接：

```text
sqlite:///项目根目录/data/gold.db
```

Docker 中使用：

```text
sqlite:////app/data/gold.db
```

`/app/data` 挂载到命名卷 `gold_data`，容器重建后数据仍会保留。

## 2. 当前表结构

### 2.1 `domestic_price`

保存国内基础金价，同时作为国内大盘没有独立缓存时的兜底。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INTEGER PK | 主键 |
| `price` | FLOAT | 元/g |
| `updated_at` | DATETIME | 更新时间 |

### 2.2 `brand_prices`

保存品牌饰品金和金条价格。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INTEGER PK | 主键 |
| `brand` | VARCHAR(50), UNIQUE | 品牌 ID |
| `brand_name` | VARCHAR(100) | 品牌中文名 |
| `gold_price` | FLOAT | 饰品金价，元/g |
| `bar_price` | FLOAT, NULL | 金条价，元/g |
| `updated_at` | DATETIME | 数据更新时间 |

当前种子品牌包括周大福、周生生、老凤祥、老庙黄金、六福珠宝、周大生和金至尊。

### 2.3 `market_prices`

保存国际和国内大盘行情缓存。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INTEGER PK | 主键 |
| `market` | VARCHAR(20) | `international` 或 `domestic` |
| `name` | VARCHAR(100) | 展示名称 |
| `symbol` | VARCHAR(50) | 行情代码 |
| `exchange` | VARCHAR(50), NULL | 交易所代码 |
| `price` | FLOAT | 最新价格 |
| `currency` | VARCHAR(10) | 币种 |
| `unit` | VARCHAR(20) | 单位 |
| `change` | FLOAT, NULL | 涨跌额 |
| `change_percent` | FLOAT, NULL | 涨跌幅百分比 |
| `source` | VARCHAR(50) | 数据来源 |
| `updated_at` | DATETIME | 行情时间 |

唯一约束：`(market, symbol)`。

API 返回的 `live / cached / fallback` 状态是读取时根据记录和时间动态计算的，不单独存储：

- 30 秒以内：`live`
- 有记录但超过 30 秒：`cached`
- 无记录：`fallback`

### 2.4 `exchange_rules`

保存门店置换规则模板。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INTEGER PK | 主键 |
| `name` | VARCHAR(100) | 模板名称 |
| `brand` | VARCHAR(50) | 品牌 ID |
| `store_name` | VARCHAR(100) | 门店或商场名称 |
| `city` | VARCHAR(100) | 城市 |
| `support_bar` | BOOLEAN | 支持金条 |
| `support_other_brand` | BOOLEAN | 支持跨品牌 |
| `support_old_jewelry` | BOOLEAN | 支持旧饰品 |
| `need_extra_gold` | BOOLEAN | 要求增金 |
| `extra_rate` | FLOAT | 增金百分比 |
| `loss_type` | VARCHAR(20) | 兼容字段，业务统一为 `percentage` |
| `loss_value` | FLOAT | 旧金每克损耗百分比 |
| `labor_type` | VARCHAR(20) | `fixed` 或 `perGram` |
| `labor_value` | FLOAT | 工费数值 |
| `recycle_price_type` | VARCHAR(20) | `recycle` 或 `jewelry` |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |

## 3. 行情缓存流程

```text
GET /api/prices
      │
      ├── 立即读取 domestic_price / brand_prices / market_prices
      │
      └── 后台刷新外部来源
                │
                ├── 成功：更新对应记录
                └── 失败：保留旧记录，不清空数据库
```

品牌刷新按来源并发执行，每个来源独立提交；单个来源异常不会回滚已经成功的品牌。

## 4. 轻量迁移策略

当前没有 Alembic。`init_db()` 使用 `create_all` 创建新表，并通过 SQLite `ALTER TABLE` 给旧规则表补充以下字段：

- `store_name VARCHAR(100) NOT NULL DEFAULT ''`
- `city VARCHAR(100) NOT NULL DEFAULT ''`

旧规则的 `loss_type` 在服务层统一按 `percentage` 读取，并在启动种子检查时写回。

后续出现复杂表变更、用户表或外键关系时，应引入 Alembic，停止继续扩展手写迁移。

## 5. 备份与恢复

本地开发可在后端停止写入后复制：

```text
data/gold.db
```

Docker 环境应备份 `gold_data` 卷。不要把运行中的数据库文件、`.env` 或 Token 提交到 Git。

`docker compose down` 保留数据；`docker compose down -v` 删除整个卷，规则模板和行情缓存均不可恢复。

## 6. 尚未实现的数据表

- 用户与登录会话。
- 用户级规则归属和共享权限。
- 计算历史与收藏方案。
- 历史金价时间序列。

这些功能仍属于后续规划，不应与浏览器 `localStorage` 中的方案自动保存混淆。
