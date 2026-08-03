# Gold Price Calculator - Frontend

Vue 3 + Vite + TypeScript 前端，包含行情首页、成本计算和门店规则管理三个页面。

## 启动

```bash
npm install
npm run dev
```

访问 <http://localhost:5173>。默认将 `/api` 代理到 <http://localhost:8000>。

## 页面

| 路径 | 功能 |
| --- | --- |
| `/` | 国际、国内和品牌金价大盘 |
| `/calculate` | 新金、旧金置换、规则选择、计算结果和多方案比较 |
| `/rules` | 门店规则模板新增、编辑和删除 |

计算页支持浏览器本地自动保存和分享链接。规则模板在计算页只读展示，只能前往规则页修改；自定义规则仅用于当前方案。

## 环境变量

本地开发通常无需创建前端环境文件。

| 变量 | 用途 |
| --- | --- |
| `VITE_API_PROXY_TARGET` | Vite 开发代理目标，默认 `http://localhost:8000` |
| `VITE_API_BASE_URL` | Axios 请求基础地址；默认空字符串，使用同源 `/api` |

如后端运行在 8001：

```powershell
$env:VITE_API_PROXY_TARGET='http://127.0.0.1:8001'
npm run dev
```

生产环境由 Nginx 把 `/api` 和 `/health` 代理到后端，无需写死后端地址。

## 构建与检查

```bash
npm run build
```

该命令先运行 `vue-tsc`，再生成 Vite 生产构建。

## 目录说明

| 目录 | 说明 |
| --- | --- |
| `src/api/` | Axios API 封装 |
| `src/assets/` | 全局样式 |
| `src/router/` | Vue Router 配置 |
| `src/types/` | API 对应的 TypeScript 类型 |
| `src/views/` | 首页、计算页和规则页 |

## 交互约定

- 首页轮询失败时保留页面最近一次成功值。
- 旧金置换关闭时隐藏旧金输入，并按直接购买计算。
- 增金条件不满足时禁止提交计算。
- 已保存模板的详情不提供输入控件。
- 用户填写的饰品实际工费优先，不强制套用同品牌统一工费。
