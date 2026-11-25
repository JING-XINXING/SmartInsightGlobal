"""全局异常处理。

错误响应统一为 {"code", "message", "data"}。
成功响应保持各端点原有结构，避免破坏已有客户端。
"""
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import logger


def error_body(code: int, message: str, data: Optional[Any] = None) -> dict:
    """构造统一错误响应体。"""
    return {"code": code, "message": message, "data": data}


def register_exception_handlers(app: FastAPI) -> None:
    """注册 HTTP、校验与未捕获异常的处理器。"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, str):
            message = detail
            data = None
        else:
            message = "请求失败"
            data = detail
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.status_code, message, data),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_body(422, "请求参数校验失败", exc.errors()),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("未处理异常 %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=error_body(500, "服务器内部错误", None),
        )
