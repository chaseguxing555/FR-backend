# 野钓记录榜 · 后端（FastAPI）

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python init_db.py
python run.py
```

- API：http://127.0.0.1:5000
- OpenAPI 文档：http://127.0.0.1:5000/docs
- 健康检查：http://127.0.0.1:5000/api/health

响应格式：`{ code, message, data }`。

完整说明见仓库根目录 [README.md](../README.md)。

## CI/CD 自动部署

本仓库独立部署。推送到 `main` 后：GitHub Actions 校验导入，再 SSH 执行 `git pull` 与 `docker compose up -d --build`。服务监听 `5000`。

### GitHub Secrets

| Secret | 说明 |
|--------|------|
| `DEPLOY_HOST` | 服务器 IP 或域名 |
| `DEPLOY_USER` | SSH 用户名 |
| `DEPLOY_SSH_KEY` | 部署用私钥全文 |
| `DEPLOY_PATH` | 服务器上的本仓库目录，如 `/opt/fishing-backend` |

### 服务器一次性准备

```bash
git clone <后端仓库地址> /opt/fishing-backend
cd /opt/fishing-backend
cp .env.example .env
# 编辑 .env：APP_ENV=production，并填写 SECRET_KEY、JWT_SECRET_KEY
docker compose up -d --build
```
