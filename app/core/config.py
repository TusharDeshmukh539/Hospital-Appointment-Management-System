from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    APP_NAME: str = "Hospital Appointment Management API"

    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    BCRYPT_ROUNDS: int = 12

    CORS_ORIGINS: str = "http://localhost:3000"

    CANCELLATION_CUTOFF_HOURS: int = 2
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 5

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()