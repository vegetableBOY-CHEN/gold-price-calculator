# 🏆 Gold Price Calculator（金价计算器）

多品牌黄金首饰价格计算工具，支持周大福、周生生、老凤祥等品牌定价规则，帮助用户计算购买成本，选择最优惠的购买方案。

---

## 📖 项目简介

Gold Price Calculator 是一个用于黄金首饰价格计算的 Web 应用，支持：

- 📈 获取各品牌当日金价
- 💰 计算黄金首饰最终购买价格
- 🔄 支持旧金置换价格计算
- 🏪 支持不同品牌不同计价规则
- ⚙️ 自定义品牌价格及规则
- 📊 多品牌价格对比

---

## 📂 项目结构

```text
gold-price-calculator/
├── frontend/          # Vue3 前端
├── backend/           # FastAPI 后端
├── rules/             # 品牌规则库（JSON）
├── docs/              # 项目文档
├── tests/             # 测试
└── scripts/           # 工具脚本
```

---

## 🚀 快速开始

### 使用 Docker（推荐）

```bash
docker-compose up -d
```

启动完成后访问：

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| Swagger 文档 | http://localhost:8000/docs |

---

### 本地开发

# 后端
cd gold-price-calculator\backend
.\venv\Scripts\activate
uvicorn app.main:app --reload

# 前端
cd gold-price-calculator\frontend
npm install
npm run dev
这能用windows运行吗


#### 后端

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

#### 前端

```bash
cd frontend

npm install

npm run dev
```

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [PRD](docs/PRD.md) | 产品需求文档 |
| [RULES](docs/RULES.md) | 品牌规则说明 |
| [API](docs/API.md) | API 接口文档 |
| [DATABASE](docs/DATABASE.md) | 数据库设计 |
| [ROADMAP](docs/ROADMAP.md) | 开发路线图 |

---

## 🛠 技术栈

### 前端

- Vue 3
- Vite
- TypeScript
- Pinia

### 后端

- FastAPI
- Pydantic

### 数据

- JSON 规则配置
- Python 规则计算引擎

---

## 📋 开发计划

- [ ] 支持实时金价同步
- [ ] 支持更多黄金品牌
- [ ] 支持旧金置换计算
- [ ] 支持优惠券、满减等活动
- [ ] 支持价格历史趋势
- [ ] 支持账号与收藏功能

---

## 📄 License

本项目采用 **MIT License**。
