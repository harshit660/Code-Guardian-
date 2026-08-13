from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    api_prefix: str = "/api/v1"
    secret_key: str = "unsafe-development-key-change-me"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite:///./codeguardian.db"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    github_token: str | None = None
    github_api_url: str = "https://api.github.com"
    llm_provider: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

