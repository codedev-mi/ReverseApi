# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    linkedin_access_token: str | None = Field(default=None, validation_alias="LINKEDIN_ACCESS_TOKEN")
    linkedin_client_id: str | None = Field(default=None, validation_alias="LINKEDIN_CLIENT_ID")
    linkedin_client_secret: str | None = Field(default=None, validation_alias="LINKEDIN_CLIENT_SECRET")
    linkedin_redirect_uri: str | None = Field(default=None, validation_alias="LINKEDIN_REDIRECT_URI")
    request_timeout: int = Field(default=20, validation_alias="REQUEST_TIMEOUT")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    cors_origins: str = Field(default="*", validation_alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()


