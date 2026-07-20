# 黄金价格计算器（Gold Price Calculator）

基于 Vue 3 与 FastAPI 的多品牌黄金首饰价格及换购成本计算工具。

## Docker 部署（推荐）

要求：Docker Engine 24+，以及 Docker Compose v2。

```bash
cp .env.example .env
# 编辑 .env，填写实际的行情服务配置
docker compose up -d --build
```

启动后可访问：

- Web 应用：<http://localhost:8080>
- API 文档：<http://localhost:8080/docs>
- 健康检查：<http://localhost:8080/health>

如需修改 Web 端口，在 `.env` 中设置 `APP_PORT`。例如 `APP_PORT=80`。

常用运维命令：

```bash
# 查看服务状态与日志
docker compose ps
docker compose logs -f

# 更新代码后重新构建
docker compose up -d --build

# 停止服务（保留数据库）
docker compose down

# 停止并删除数据库卷（会永久删除应用数据）
docker compose down -v
```

SQLite 数据保存在 Docker 命名卷 `gold_data` 中；`rules/` 目录以只读方式挂载到后端容器。`.env` 不会进入镜像构建上下文，也不应提交到版本库。

## 本地开发

后端：

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```text
gold-price-calculator/
├── frontend/          # Vue 3 前端与 Nginx 配置
├── backend/           # FastAPI 后端
├── rules/             # 品牌规则库（JSON）
├── docs/              # 项目文档
├── tests/             # 测试
└── scripts/           # 工具脚本
```

## 技术栈

- 前端：Vue 3、Vite、TypeScript、Pinia、Nginx
- 后端：FastAPI、Pydantic、SQLAlchemy、SQLite
- 部署：Docker、Docker Compose

## License

MIT
