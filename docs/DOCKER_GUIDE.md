# 黄金价格计算器 Docker 学习与操作手册

这份文档整理本项目从本地构建、Docker Compose 运行、日常维护，到上传 Docker Hub 和服务器部署的完整操作。

> 项目目录：`E:\1-work\gold\gold-price-calculator`
>
> Docker Hub 用户名：`vegetableboy`
>
> 安全提醒：本文不记录任何真实 AllTick Token 或 Docker Hub Token。

## 1. Docker 基础概念

### 1.1 镜像（Image）

镜像类似“软件安装包”，里面包含应用代码、运行环境、依赖和启动命令。

本项目有两个应用镜像：

```text
gold-price-calculator-frontend:latest
gold-price-calculator-backend:latest
```

### 1.2 容器（Container）

容器是镜像运行起来后的实例。镜像本身不会处理请求，容器才是正在运行的程序。

### 1.3 数据卷（Volume）

容器删除后，其内部数据可能消失。数据卷用于持久保存 SQLite 数据库等重要数据。

生产配置中使用的数据卷名称通常为：

```text
gold-price-calculator_gold_data
```

### 1.4 Docker Compose

Compose 使用一个 YAML 文件同时管理前端、后端、端口、网络、环境变量和数据卷。

本项目使用：

```text
docker-compose.yml
```

## 2. 本项目的运行结构

```text
浏览器 http://localhost:8080
             │
             ▼
       前端容器（Nginx）
       │                 │
       │ 静态页面        │ /api、/health
       │                 ▼
       │         后端容器（FastAPI）
       │                 │
       │                 ▼
       │          SQLite 数据卷
       │          ├── 行情与品牌价格缓存
       │          └── 门店规则模板
       │
       └── Vue 编译后的 HTML/CSS/JS
```

生产部署相关文件通常包括：

```text
docker-compose.yml
backend/Dockerfile
frontend/Dockerfile
frontend/nginx.conf
.dockerignore
.env
.env.example
```

使用生产部署命令前，应先通过 `git branch --show-current` 和 `git status` 确认当前分支、未提交改动及 Docker 配置。

### 2.1 行情请求与数据卷

`GET /api/prices` 会先读取 SQLite 数据卷中的最近价格，再由后台任务刷新第三方行情。因此：

- AllTick Token 缺失、过期或网络暂时不可用时，页面仍可显示数据库缓存和初始化兜底值。
- 品牌来源按品牌独立刷新，单个来源失败不会删除其他品牌价格。
- 删除 `gold_data` 卷会同时删除行情缓存和门店规则，不只是删除“临时数据”。
- 容器重建后首次访问可能先显示缓存，后台刷新成功后的下一次请求才会看到新值。

## 3. Dockerfile 是什么

Dockerfile 是构建镜像的说明书。

### 3.1 后端 Dockerfile

典型后端 Dockerfile 会完成：

1. 选择 Python 基础镜像。
2. 设置工作目录。
3. 安装 Python 依赖。
4. 复制 FastAPI 代码。
5. 创建普通运行用户。
6. 配置健康检查。
7. 使用 Uvicorn 启动服务。

示例：

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY rules ./rules

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 前端 Dockerfile

Vue 前端推荐使用多阶段构建：

1. Node.js 阶段安装依赖并执行 `npm run build`。
2. Nginx 阶段只保留编译后的 `dist` 文件。

示例：

```dockerfile
FROM node:20-alpine AS build

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

多阶段构建的优点：

- 最终镜像不需要完整 Node.js 开发环境。
- 镜像更小。
- 运行环境更简单。
- 更适合生产部署。

## 4. Nginx 反向代理

浏览器访问：

```text
http://localhost:8080/api/prices
```

Nginx 会把请求转发到 Docker 网络中的后端服务：

```text
http://backend:8000/api/prices
```

示例配置：

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location = /health {
        proxy_pass http://backend:8000/health;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

`backend` 不是互联网域名，而是 Compose 中的服务名。Docker 内部 DNS 会自动解析它。

## 5. `.env` 环境变量

`.env` 保存运行时配置，例如：

```env
APP_PORT=8080
ALLTICK_TOKEN=你的真实Token
ALLTICK_BASE_URL=https://quote.alltick.co
ALLTICK_TIMEOUT_SECONDS=12
ALLTICK_INTERNATIONAL_SYMBOLS=GOLD::国际现货黄金:USD/oz
ALLTICK_DOMESTIC_SYMBOLS=AU9999:SGE:上海金 AU9999:CNY/g
```

品种格式为 `symbol:exchange:展示名称:币种/单位`。`ALLTICK_TOKEN` 可以留空；留空时国际实时行情可能不可用，但应用会继续使用数据库缓存和其他可用来源。

重要规则：

- 不要把真实 Token 写入 `.env.example`。
- 不要把 `.env` 提交到 GitHub。
- 不要随意用 `.env.example` 覆盖已经配置好的 `.env`。
- 不要把 Token 直接写进 Dockerfile。
- 修改 `.env` 后需要重新创建容器。

编辑 `.env`：

```powershell
notepad .env
```

使新环境变量生效：

```powershell
docker compose up -d --force-recreate
```

## 6. `.dockerignore` 的作用

`.dockerignore` 控制哪些文件不进入 Docker 构建上下文。

推荐排除：

```text
.git
.env
node_modules
dist
__pycache__
.pytest_cache
*.db
*.log
.idea
.vscode
```

它可以：

- 防止 `.env` 和 Token 被打进镜像。
- 减少构建上下文大小。
- 加快构建速度。
- 避免把本地缓存和数据库上传到镜像。

## 7. 第一次构建和启动

### 7.1 启动 Docker Desktop

先启动 Docker Desktop，等待 Docker Engine 就绪。

检查：

```powershell
docker version
```

如果输出中同时有 Client 和 Server，说明 Docker Engine 可以使用。

### 7.2 进入项目目录

```powershell
cd E:\1-work\gold\gold-price-calculator
```

### 7.3 构建并启动

```powershell
docker compose up -d --build
```

参数说明：

- `up`：创建并启动服务。
- `-d`：后台运行。
- `--build`：启动前重新构建镜像。

### 7.4 查看状态

```powershell
docker compose ps
```

生产配置正常时应看到：

```text
backend    Up ... (healthy)
frontend   Up ... (healthy)
```

### 7.5 访问服务

- Web：<http://localhost:8080>
- API 文档：<http://localhost:8080/docs>
- 健康检查：<http://localhost:8080/health>

如果当前 Compose 仍是开发配置，前端端口可能是 `5173`，应以 `docker compose ps` 显示的端口为准。

## 8. 日常更新和重新部署

```powershell
cd E:\1-work\gold\gold-price-calculator
git status
git pull origin main
docker compose up -d --build
docker compose ps
```

操作含义：

1. 检查本地是否有未提交修改。
2. 获取 GitHub 最新代码。
3. 重新构建发生变化的镜像。
4. 使用新镜像替换旧容器。
5. 检查容器是否健康。

如果 `git pull` 提示本地文件将被覆盖，不要直接执行：

```text
git reset --hard
```

它可能永久删除未提交修改。应先使用 `git status` 判断哪些文件发生冲突。

## 9. 常用运维命令

查看服务状态：

```powershell
docker compose ps
```

查看所有实时日志：

```powershell
docker compose logs -f
```

只看后端日志：

```powershell
docker compose logs -f backend
```

只看前端日志：

```powershell
docker compose logs -f frontend
```

停止服务并保留数据库：

```powershell
docker compose down
```

再次启动：

```powershell
docker compose up -d
```

重启服务：

```powershell
docker compose restart
```

查看镜像：

```powershell
docker images
```

查看实时 CPU 和内存：

```powershell
docker stats
```

查看 Docker 磁盘占用：

```powershell
docker system df
docker system df -v
```

查看数据卷：

```powershell
docker volume ls
```

删除容器并同时删除数据卷：

```powershell
docker compose down -v
```

> `docker compose down -v` 会删除本项目数据库卷，除非确认数据不再需要，否则不要执行。

## 10. 镜像占用硬盘还是内存

`docker images` 中的镜像主要占用硬盘空间，不是运行内存。

运行中的容器才会占用 RAM，可以通过以下命令查看：

```powershell
docker stats
```

多个标签如果对应相同的 `IMAGE ID`，只是多个名称指向同一份镜像数据，通常不会重复占用完整磁盘空间。

例如：

```text
gold-price-calculator-frontend:latest
vegetableboy/gold-price-calculator-frontend:latest
vegetableboy/gold-price-calculator-frontend:v1.0.0
```

如果三个名称的 `IMAGE ID` 相同，它们共享同一份镜像内容。

## 11. 上传镜像到 Docker Hub

### 11.1 创建 Docker Hub 仓库

登录 <https://hub.docker.com/>，进入：

```text
My Hub → Repositories → Create repository
```

创建两个仓库：

```text
vegetableboy/gold-price-calculator-frontend
vegetableboy/gold-price-calculator-backend
```

仓库可选择：

- `Public`：任何人都能拉取。
- `Private`：只有授权用户能拉取。

### 11.2 创建 Personal Access Token

在 Docker Hub 账户设置中创建具有 Read/Write 权限的 Personal Access Token。

不要将 Token：

- 写进项目文件。
- 写进 Dockerfile。
- 提交到 GitHub。
- 直接放在命令参数中。

### 11.3 登录 Docker Hub

```powershell
docker login --username vegetableboy
```

终端显示 `Password:` 时粘贴 Personal Access Token。输入内容不会显示，按回车即可。

成功提示：

```text
Login Succeeded
```

### 11.4 构建最新镜像

```powershell
cd E:\1-work\gold\gold-price-calculator
docker compose build
docker images
```

确认存在：

```text
gold-price-calculator-frontend:latest
gold-price-calculator-backend:latest
```

### 11.5 添加 Docker Hub 标签

前端：

```powershell
docker tag gold-price-calculator-frontend:latest vegetableboy/gold-price-calculator-frontend:v1.0.0
docker tag gold-price-calculator-frontend:latest vegetableboy/gold-price-calculator-frontend:latest
```

后端：

```powershell
docker tag gold-price-calculator-backend:latest vegetableboy/gold-price-calculator-backend:v1.0.0
docker tag gold-price-calculator-backend:latest vegetableboy/gold-price-calculator-backend:latest
```

标签格式：

```text
DockerHub用户名/仓库名:版本号
```

### 11.6 检查标签是否正确

```powershell
docker images
```

必须确认：

- `vegetableboy/gold-price-calculator-frontend:*` 的 IMAGE ID 与本地前端一致。
- `vegetableboy/gold-price-calculator-backend:*` 的 IMAGE ID 与本地后端一致。
- 不要把前端镜像误标记成后端 `latest`。

如果后端 `latest` 错误指向了前端镜像，修正：

```powershell
docker tag gold-price-calculator-backend:latest vegetableboy/gold-price-calculator-backend:latest
```

### 11.7 推送镜像

前端：

```powershell
docker push vegetableboy/gold-price-calculator-frontend:v1.0.0
docker push vegetableboy/gold-price-calculator-frontend:latest
```

后端：

```powershell
docker push vegetableboy/gold-price-calculator-backend:v1.0.0
docker push vegetableboy/gold-price-calculator-backend:latest
```

成功后会显示类似：

```text
v1.0.0: digest: sha256:...
```

然后在 Docker Hub 仓库的 `Tags` 页面确认 `v1.0.0` 和 `latest` 存在。

## 12. 发布后续版本

例如发布 `v1.1.0`：

```powershell
git pull origin main
docker compose build

docker tag gold-price-calculator-frontend:latest vegetableboy/gold-price-calculator-frontend:v1.1.0
docker tag gold-price-calculator-backend:latest vegetableboy/gold-price-calculator-backend:v1.1.0

docker push vegetableboy/gold-price-calculator-frontend:v1.1.0
docker push vegetableboy/gold-price-calculator-backend:v1.1.0
```

更新 `latest`：

```powershell
docker tag gold-price-calculator-frontend:latest vegetableboy/gold-price-calculator-frontend:latest
docker tag gold-price-calculator-backend:latest vegetableboy/gold-price-calculator-backend:latest

docker push vegetableboy/gold-price-calculator-frontend:latest
docker push vegetableboy/gold-price-calculator-backend:latest
```

建议保留明确版本，例如：

```text
v1.0.0
v1.1.0
v2.0.0
```

不要只依赖 `latest`，明确版本更方便回退。

## 13. 从 Docker Hub 下载镜像

```powershell
docker pull vegetableboy/gold-price-calculator-frontend:v1.0.0
docker pull vegetableboy/gold-price-calculator-backend:v1.0.0
```

如果仓库是 Private，需要先登录：

```powershell
docker login --username vegetableboy
```

## 14. 服务器使用 Docker Hub 镜像

服务器不需要源代码时，可以使用只包含 `image` 的 Compose 配置：

```yaml
services:
  backend:
    image: vegetableboy/gold-price-calculator-backend:v1.0.0
    restart: unless-stopped
    env_file:
      - .env
    environment:
      DEBUG: "false"
      DATABASE_URL: sqlite:////app/data/gold.db
    volumes:
      - gold_data:/app/data
    expose:
      - "8000"

  frontend:
    image: vegetableboy/gold-price-calculator-frontend:v1.0.0
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "8080:80"

volumes:
  gold_data:
```

服务器操作：

```bash
docker compose pull
docker compose up -d
docker compose ps
```

更新到新版本时修改镜像版本，然后再次执行：

```bash
docker compose pull
docker compose up -d
```

## 15. 常见故障排查

### 15.1 Docker Engine 未启动

错误类似：

```text
failed to connect to the docker API
```

解决：启动 Docker Desktop，等待引擎就绪，然后执行：

```powershell
docker version
```

### 15.2 Docker Hub 基础镜像下载失败

如果 Docker Hub 网络异常，可以临时使用可信镜像代理，例如通过 Dockerfile 参数：

```dockerfile
ARG DOCKER_REGISTRY=docker.1ms.run/library
FROM ${DOCKER_REGISTRY}/python:3.11-slim
```

镜像代理的可用性会变化，生产环境应优先保证官方 Docker Hub 或可信私有仓库可访问。

### 15.3 npm 出现 `ECONNRESET`

可增加下载重试：

```dockerfile
RUN npm config set registry https://registry.npmmirror.com \
    && npm config set fetch-retries 5 \
    && npm config set fetch-retry-mintimeout 10000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && npm ci
```

### 15.4 GitHub 拉取失败

Clash Verge 当时可用代理端口为 `7897`：

```powershell
git config --local http.proxy http://127.0.0.1:7897
git config --local https.proxy http://127.0.0.1:7897
```

验证：

```powershell
git pull origin main
```

如果 Clash Verge 端口改变，需要同步修改。该配置只影响当前仓库。

### 15.5 Docker Hub 提示没有权限

错误类似：

```text
requested access to the resource is denied
```

检查：

- 是否使用 `vegetableboy` 登录。
- Docker Hub 仓库是否已创建。
- Token 是否具有 Write 权限。
- 镜像名称中的用户名是否正确。
- 前后端仓库名称是否拼写正确。

重新登录：

```powershell
docker logout
docker login --username vegetableboy
```

### 15.6 Docker Hub 推送超时

检查 Clash Verge 和 Docker Desktop 代理后，重新执行相同的 `docker push`。已经上传成功的镜像层通常会显示：

```text
Layer already exists
```

不需要重新上传全部内容。

## 16. 常用命令速查

### 本地构建并启动

```powershell
docker compose up -d --build
```

### 查看状态

```powershell
docker compose ps
```

### 查看日志

```powershell
docker compose logs -f
```

### 更新代码并重新部署

```powershell
git pull origin main
docker compose up -d --build
docker compose ps
```

### 停止并保留数据

```powershell
docker compose down
```

### 上传 v1.0.0

```powershell
docker login --username vegetableboy
docker compose build

docker tag gold-price-calculator-frontend:latest vegetableboy/gold-price-calculator-frontend:v1.0.0
docker tag gold-price-calculator-backend:latest vegetableboy/gold-price-calculator-backend:v1.0.0

docker push vegetableboy/gold-price-calculator-frontend:v1.0.0
docker push vegetableboy/gold-price-calculator-backend:v1.0.0
```

## 17. 安全注意事项

- 不要提交 `.env`。
- 不要公开 AllTick Token 或 Docker Hub Token。
- 不要使用 `docker login -p 明文Token`。
- 不要把 Token 写进 Dockerfile 或镜像。
- 当前规则和金价写接口没有登录鉴权，不要在没有反向代理访问控制的情况下直接暴露后端 8000 端口。
- 不要随意执行 `docker compose down -v`。
- 不要随意执行 `docker system prune -a`。
- 不要随意执行 `git reset --hard`。
- 上传前检查前后端镜像的 IMAGE ID，防止标签打错。
- 生产发布建议使用明确版本标签，不要只使用 `latest`。
