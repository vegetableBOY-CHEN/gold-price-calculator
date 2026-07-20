ARG DOCKER_REGISTRY=docker.1ms.run/library
FROM ${DOCKER_REGISTRY}/node:20-alpine AS build

WORKDIR /app

COPY frontend/package*.json ./
RUN npm config set registry https://registry.npmmirror.com \
    && npm config set fetch-retries 5 \
    && npm config set fetch-retry-mintimeout 10000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && npm ci

COPY frontend/ ./
RUN npm run build

FROM ${DOCKER_REGISTRY}/nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -q --spider http://127.0.0.1/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
