from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = "ERROR"
    if exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 422:
        code = "VALIDATION_ERROR"
    detail = exc.detail if isinstance(exc.detail, str) else "Ошибка запроса"
    return JSONResponse(status_code=exc.status_code, content=error_body(code, detail))


async def validation_exception_handler(request: Request, exc):
    message = "Проверьте корректность полей"
    errors = getattr(exc, "errors", None)
    if callable(errors):
        first = errors()[0] if errors() else None
        if first and "msg" in first:
            message = f"{'.'.join(map(str, first.get('loc', [])))}: {first['msg']}"
    return JSONResponse(status_code=422, content=error_body("VALIDATION_ERROR", message))
