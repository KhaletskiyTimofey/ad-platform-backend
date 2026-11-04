from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://adplatform:adplatform@db:5432/adplatform"
    SESSION_SECRET: str = "change-me"
    SESSION_TTL_DAYS: int = 7

    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "media"
    MINIO_PUBLIC_URL: str = "http://localhost:9000"

    PUBLIC_BASE_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:4173"

    MAX_IMAGE_BYTES: int = 5 * 1024 * 1024
    MAX_VIDEO_BYTES: int = 30 * 1024 * 1024
    MAX_HTML_BYTES: int = 1 * 1024 * 1024


settings = Settings()
