from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import init_db
from app.errors import http_exception_handler, validation_exception_handler
from app.routers import auth, billing, campaigns, uploads
from app.storage import ensure_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        ensure_bucket()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] MinIO not ready: {exc}")
    yield


app = FastAPI(title="AdPulse API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(auth.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
