from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "AI Document Processing API"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"

    secret_key: str = Field(default="change-this-secret-key")
    access_token_expire_minutes: int = 1440

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "document_processing"
    mysql_user: str = "doc_user"
    mysql_password: str = "doc_password"

    aws_region: str = "ap-south-1"
    aws_s3_bucket_name: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_presigned_url_expire_seconds: int = 300

    bedrock_model_id: str = "amazon.nova-micro-v1:0"
    bedrock_max_tokens: int = 1200
    bedrock_temperature: float = 0.2

    max_files_per_upload: int = 3
    max_file_size_mb: int = 5

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
