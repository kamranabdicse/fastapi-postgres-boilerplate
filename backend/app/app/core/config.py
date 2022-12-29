import secrets

from pydantic import BaseSettings


class Settings(BaseSettings):
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str

    class Config:
        env_file = ".env"


settings = Settings()