from pydantic_settings import BaseSettings
from pydantic import computed_field
from typing import Literal


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Turnip Exchanger"
    APP_ENV: Literal["development", "production", "testing"] = "development"
    SECRET_KEY: str

    # Database
    DATABASE_URL: str

    # OAuth - Discord
    DISCORD_CLIENT_ID: str
    DISCORD_CLIENT_SECRET: str
    DISCORD_REDIRECT_URI: str

    # OAuth - Google
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    @computed_field
    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
