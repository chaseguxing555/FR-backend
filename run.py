"""
@file run.py
@description 开发环境启动入口（uvicorn + FastAPI）
@module run
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

import uvicorn


if __name__ == "__main__":
    # 开发模式监听 0.0.0.0:5000，热重载
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
    )
