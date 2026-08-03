# 黄金价格计算器（Gold Price Calculator）

基于 Vue 3、FastAPI 和 SQLite 的黄金行情与旧金置换成本计算工具。项目用于查看国内外大盘及品牌金价，维护门店置换规则，并比较多个购买方案的真实成本和克均价。

## 当前功能

- 首页展示国际大盘、国内大盘、品牌饰品金和金条价格。
- 行情接口优先返回 SQLite 最近缓存，再在后台刷新外部数据；外部 API 暂时失效时不会阻塞首页。
- 品牌价格按来源独立刷新，单个品牌获取失败不会影响其他品牌或数据库中的历史价格。
- 支持直接购买和旧金置换两种计算方式。
- 旧金可选择“饰品 / 金条”，并保留旧金购买成本用于计算真实成本。
- 旧金损耗统一按旧金重量的百分比计算。
- 门店规则支持增金要求、适用品类、跨品牌、工费和回收计价等配置。
- 勾选“要求增金”后必须填写增金比例；实际增金不足时禁止计算并给出所需重量提示。
- 规则模板支持城市、门店或商场名称，并存储在 SQLite 中。
- 计算页会只读展示所选规则模板的具体内容；修改模板需前往“规则”页面。
- 支持多方案创建、复制、比较、本地自动保存和分享链接。

## 行情数据策略

`GET /api/prices` 是缓存优先接口：

1. 立即读取 SQLite 中的大盘、品牌和更新时间。
2. 在后台尝试刷新大盘行情和已过期的品牌价格。
3. 刷新成功后写回数据库，下一次请求即可读取新值。
4. 外部来源不可用时继续返回最近缓存或初始化兜底值。

首页会把大盘状态标记为“实时”“缓存”或“兜底”。AllTick Token 可以留空；此时国际实时行情可能不可用，但数据库缓存、国内行情兜底和品牌价格仍可正常展示。

## Docker 部署（推荐）

要求：Docker Engine 24+、Docker Compose v2。

```bash
cp .env.example .env
# 按需填写 ALLTICK_TOKEN；不使用 AllTick 时可以留空
docker compose up -d --build
```

启动后访问：

- Web 应用：<http://localhost:8080>
- API 文档：<http://localhost:8080/docs>
- 健康检查：<http://localhost:8080/health>

如需修改 Web 端口，在 `.env` 中设置 `APP_PORT`。

```bash
docker compose ps
docker compose logs -f
docker compose up -d --build
docker compose down
```

SQLite 数据保存在 Docker 命名卷 `gold_data` 中。`docker compose down -v` 会永久删除该卷中的价格缓存和规则模板，请谨慎使用。

## 本地开发

后端：

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

默认地址：前端 <http://localhost:5173>，后端 <http://localhost:8000>。开发服务器会把 `/api` 代理到后端。

## 验证

```bash
# 仓库根目录运行后端测试
pytest -q

# 前端类型检查与生产构建
cd frontend
npm run build
```

当前测试覆盖 API、规则 CRUD、增金校验、旧金损耗计算、行情缓存读取和外部来源局部失败等场景。

## 项目结构

```text
gold-price-calculator/
├── frontend/          # Vue 3 前端、路由和 Nginx 配置
├── backend/           # FastAPI、计算引擎、服务和 SQLite 模型
├── data/              # 本地 SQLite 数据（默认 data/gold.db）
├── rules/             # 早期品牌规则 JSON 与示例，当前门店模板以数据库为准
├── docs/              # PRD、API、数据库、规则和部署文档
├── tests/             # 后端自动化测试
└── scripts/           # 工具脚本
```

## 文档

- [产品需求](docs/PRD.md)
- [API 文档](docs/API.md)
- [数据库设计](docs/DATABASE.md)
- [门店规则说明](docs/RULES.md)
- [开发路线图](docs/ROADMAP.md)
- [Docker 操作手册](docs/DOCKER_GUIDE.md)
- [Git 操作指南](docs/GIT_GUIDE.md)

## 当前边界

- 外部实时行情依赖第三方服务可用性，缓存值不等同于实时成交价。
- 门店规则目前是应用级共享数据，尚未接入账户和用户级规则隔离。
- 金价维护和规则 CRUD API 当前没有登录鉴权，公网部署前应增加访问控制。
- 暂未提供计算历史、规则云同步、金价走势和价格提醒。
- 计算结果用于购买方案比较，不构成投资建议或门店正式报价。

## 技术栈

- 前端：Vue 3、Vite、TypeScript、Vue Router、Axios
- 后端：FastAPI、Pydantic、SQLAlchemy、SQLite、HTTPX
- 部署：Docker、Docker Compose、Nginx

## License

MIT
