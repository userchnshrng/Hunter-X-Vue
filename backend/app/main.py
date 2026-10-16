import logging
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.api import auth, files, records
from app.core.config import Settings, settings
from app.core.database import make_engine

logger = logging.getLogger("hunter")


def create_app(config: Settings = settings):
    @asynccontextmanager
    async def lifespan(app):
        yield
        app.state.engine.dispose()

    app = FastAPI(title="Hunter 猎头工作台", version="0.1.0", lifespan=lifespan)
    app.state.settings = config
    app.state.engine = make_engine(config.database_url)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = secrets.token_hex(8)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    def error(request, status, message, code=None, details=None):
        return JSONResponse(
            status_code=status,
            content={
                "code": code or f"HTTP_{status}",
                "message": message,
                "details": details,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error(request, exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Do not echo supplied passwords, full resumes or arbitrary request bodies.
        details = [
            {"field": ".".join(map(str, item["loc"][1:])), "message": item["msg"]} for item in exc.errors()
        ]
        return error(request, 422, "请检查表单内容", details=jsonable_encoder(details))

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, exc):
        return error(request, 409, "记录关联或唯一性冲突，请刷新后重试")

    @app.exception_handler(OperationalError)
    async def database_error(request, exc):
        return error(request, 503, "数据库不可用或尚未初始化，请检查本地启动说明")

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logger.error("request_failed request_id=%s type=%s", request.state.request_id, type(exc).__name__)
        return error(request, 500, "服务暂时无法处理该请求，请稍后重试")

    @app.get("/api/v1/health", tags=["health"])
    def health():
        with app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            ready = inspect(connection).has_table("alembic_version")
        if not ready:
            raise HTTPException(503, "请先执行初始数据库迁移")
        return {"status": "ok", "database": app.state.engine.dialect.name, "stage": "A"}

    for router in (auth.router, records.router, files.router):
        app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
