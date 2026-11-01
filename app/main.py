from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, balance, campaigns, stats
from app.storage import ensure_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        ensure_bucket()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] MinIO not ready: {exc}")
    yield


app = FastAPI(title="AdPlatform API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(balance.router, prefix="/api")
app.include_router(stats.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
