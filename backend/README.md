# Gold Price Calculator - Backend

FastAPI 后端服务，提供金价查询、品牌规则解析与价格计算 API。

## 启动

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API 文档

启动后访问 http://localhost:8000/docs

## 目录说明

| 目录 | 说明 |
|------|------|
| `app/api/` | 路由与请求处理 |
| `app/services/` | 业务逻辑层 |
| `app/calculator/` | 价格计算引擎 |
| `app/models/` | Pydantic 数据模型 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RULES_DIR` | `../rules` | 品牌规则 JSON 目录 |
| `CORS_ORIGINS` | `http://localhost:5173` | 允许的前端来源 |
