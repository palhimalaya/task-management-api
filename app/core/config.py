from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    APP_ENV: str = "development"
    APP_TITLE: str = "Task Management API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "A role-based task management system with JWT authentication. "
        "Supports ADMIN, MANAGER, and USER roles with fine-grained permissions."
    )

    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
