import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'WishList'
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:4521@localhost:5432/wishlist")
    secret_key: str = os.getenv("SECRET_KEY", "supersecretkey")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", 587))
    smtp_user: str = os.getenv("SMTP_USER", "user@example.com")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "password")

    smtp_from: str = os.getenv("SMTP_FROM", "noreply@yourapp.com")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
