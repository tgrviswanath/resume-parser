from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Resume Parser API"
    APP_VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: list = ["http://localhost:3000"]
    NLP_SERVICE_URL: str = "http://localhost:8001"

    class Config:
        env_file = ".env"


settings = Settings()
