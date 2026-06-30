# 金价计算器 (Gold Price Calculator)

多品牌黄金首饰价格计算工具，支持周大福、周生生、老凤祥等品牌定价规则。

## 项目结构

```
gold-price-calculator/
├── frontend/          # Vue3 前端
├── backend/           # FastAPI 后端
├── rules/             # 品牌规则库 (JSON)
├── docs/              # 项目文档
├── tests/             # 测试
└── scripts/           # 工具脚本
```

## 快速开始

### 使用 Docker（推荐）

```bash
docker-compose up -d
```

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 本地开发

**后端**

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**前端**

```bash
cd frontend
npm install
npm run dev
```

## 文档

| 文档 | 说明 |
|------|------|
| [docs/PRD.md](docs/PRD.md) | 产品需求 |
| [docs/RULES.md](docs/RULES.md) | 品牌规则说明 |
| [docs/API.md](docs/API.md) | API 接口文档 |
| [docs/DATABASE.md](docs/DATABASE.md) | 数据库设计 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 开发路线图 |

## 技术栈

- **前端**: Vue 3 + Vite + TypeScript + Pinia
- **后端**: FastAPI + Pydantic
- **规则引擎**: JSON 配置 + Python 计算器

## License

MIT
