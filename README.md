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
