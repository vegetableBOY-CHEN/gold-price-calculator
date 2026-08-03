# Gold Price Calculator - Backend

FastAPI 后端，负责行情缓存与刷新、门店规则 CRUD、SQLite 持久化和旧金置换成本计算。

## 启动

从 `backend/` 目录执行：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

启动时会创建数据库表、执行轻量字段迁移，并在空表中写入价格和规则种子数据。

## API

- Swagger UI：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>
- 金价概览：`GET /api/prices`
- 手动更新金价：`PUT /api/prices`
- 规则管理：`/api/rules`
- 成本计算：`POST /api/calculate`

完整说明见 [`../docs/API.md`](../docs/API.md)。

## 行情刷新模型

`GET /api/prices` 只读取 SQLite，不同步访问第三方来源。响应返回后，FastAPI 后台任务尝试刷新：

- 大盘行情：最多每 5 秒发起一次刷新。
- 品牌价格：记录超过 8 小时或仍是种子值时刷新。
- AllTick：可选，用于配置的国际和国内品种。
- 新浪：国内 AU9999 兜底来源。
- 品牌官方或公开页面：周大福、周生生、六福及其他已配置品牌。

所有来源失败时保留数据库旧值，不会因为刷新失败清空首页数据。

## 目录说明

| 目录 | 说明 |
| --- | --- |
| `app/api/` | FastAPI 路由 |
| `app/calculator/` | 旧金置换计算引擎 |
| `app/db/` | SQLAlchemy Engine、模型和轻量迁移 |
| `app/models/` | Pydantic 请求与响应模型 |
| `app/services/` | 行情、规则和计算服务 |

## 环境变量

后端默认读取项目根目录 `.env`，未知变量会被忽略。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_NAME` | `Gold Price Calculator` | 应用名称 |
| `DEBUG` | `true` | 调试模式 |
| `DATABASE_URL` | `sqlite:///.../data/gold.db` | SQLAlchemy 数据库连接 |
| `CORS_ORIGINS` | 本地 5173 地址 | JSON 数组形式的允许来源 |
| `RULES_DIR` | 项目 `rules/` | 兼容早期 JSON 规则目录；当前门店模板在数据库中 |
| `ALLTICK_TOKEN` | 空 | AllTick Token，可不配置 |
| `ALLTICK_BASE_URL` | `https://quote.alltick.co` | AllTick 基础地址 |
| `ALLTICK_TIMEOUT_SECONDS` | `12` | 配置值；单次大盘请求当前最多等待 3 秒 |
| `ALLTICK_INTERNATIONAL_SYMBOLS` | `GOLD::国际现货黄金:USD/oz` | 逗号分隔的品种配置 |
| `ALLTICK_DOMESTIC_SYMBOLS` | `AU9999:SGE:上海金 AU9999:CNY/g` | 逗号分隔的品种配置 |

品种格式为：

```text
symbol:exchange:display name:currency/unit
```

交易所为空时保留连续两个冒号，例如 `GOLD::国际现货黄金:USD/oz`。

## 测试

从仓库根目录执行：

```bash
pytest -q
```

测试使用临时 SQLite 数据库，不会修改 `data/gold.db`。
