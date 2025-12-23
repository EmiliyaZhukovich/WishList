import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = 'WishList'
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:4521@localhost:5432/wishlist")
    secret_key: str = os.getenv("SECRET_KEY", "supersecretkey")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    class Config:
        env_file = '.env'

settings = Settings()
