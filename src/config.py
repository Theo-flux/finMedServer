from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str

    EMAIL_SALT: str

    DEFAULT_PAGE_MIN_LIMIT: int = 1
    DEFAULT_PAGE_MAX_LIMIT: int = 100
    DEFAULT_PAGE_LIMIT: int = 30
    DEFAULT_PAGE_OFFSET: int = 0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


Config = Settings()
