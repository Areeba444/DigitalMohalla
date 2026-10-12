"""Runtime settings read from environment variables (or a local .env file).

Engine parameters are NOT here: they live in the versioned file config/engine.json
(see engine_config.py). Only deployment-specific values such as the database URL are settings.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # e.g. postgresql+psycopg://user:password@localhost:5433/digitalmohalla (see .env.example)
    database_url: str | None = None
    # signs login tokens; set a long random value in .env (never commit it)
    jwt_secret: str | None = None
    jwt_minutes: int = 60
    # browsers allowed to call the API (the Expo web dev server); comma separated
    cors_origins: str = "http://localhost:8081,http://localhost:19006"
    # any localhost port is also allowed by default, because Expo moves to another port when 8081
    # is busy; set to an empty string in deployment and list real origins in cors_origins
    cors_origin_regex: str = r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"


@lru_cache
def get_settings() -> Settings:
    return Settings()
