# 金价计算器 (Gold Price Calculator)

多品牌黄金首饰价格与置换成本计算工具。首页展示国际、国内大盘价格和各大黄金店铺饰品金价格，计算页用于评估换购成本。

## 项目结构

```text
gold-price-calculator/
├── frontend/          # Vue 3 前端
├── backend/           # FastAPI 后端
├── rules/             # 品牌规则库 (JSON)
├── docs/              # 项目文档
├── tests/             # 测试
└── scripts/           # 工具脚本
```

## 快速开始

### 使用 Docker

```bash
docker-compose up -d
```

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 本地开发

后端:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

前端:

```bash
cd frontend
npm install
npm run dev
```

## 实时行情配置

后端支持接入 AllTick HTTP 最新价接口。未配置 token 或请求失败时，接口会返回本地兜底价格，并在响应里标记 `status: "fallback"`。

在项目根目录 `.env` 中配置:

```env
ALLTICK_TOKEN=your_token
ALLTICK_BASE_URL=https://quote.alltick.io
ALLTICK_INTERNATIONAL_SYMBOLS=XAUUSD:OANDA:国际现货黄金:USD/oz
ALLTICK_DOMESTIC_SYMBOLS=AU9999:SGE:上海金 AU9999:CNY/g
```

`*_SYMBOLS` 格式为 `code:exchange:name:currency/unit`，多个品种用英文逗号分隔。实际 `code` 和 `exchange` 请按 AllTick 后台开通的数据源调整。

## 文档

| 文档 | 说明 |
|------|------|
| [docs/PRD.md](docs/PRD.md) | 产品需求 |
| [docs/RULES.md](docs/RULES.md) | 品牌规则说明 |
| [docs/API.md](docs/API.md) | API 接口文档 |
| [docs/DATABASE.md](docs/DATABASE.md) | 数据库设计 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 开发路线图 |

## 技术栈

- 前端: Vue 3 + Vite + TypeScript + Pinia
- 后端: FastAPI + Pydantic + SQLAlchemy
- 行情源: AllTick 可配置接入，本地价格兜底
- 规则引擎: JSON 配置 + Python 计算器

## License

MIT
