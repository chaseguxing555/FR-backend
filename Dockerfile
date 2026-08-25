# @file Dockerfile
# @description 后端生产镜像：Uvicorn 运行 FastAPI
# @module backend
# @author fishing-ranking
# @created 2026-08-25
# @updated 2026-08-25
# @version 1.0.0

FROM python:3.12-slim

WORKDIR /app

# 先装依赖，避免源码变更时重复下载
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 上传目录与 SQLite 目录在容器内必须存在
RUN mkdir -p /app/uploads /app/instance

EXPOSE 5000

# 生产关闭热重载，由 docker compose 注入环境变量
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
