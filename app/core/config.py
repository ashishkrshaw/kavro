from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REDIS_URL: str
    ENCRYPTION_KEY: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
