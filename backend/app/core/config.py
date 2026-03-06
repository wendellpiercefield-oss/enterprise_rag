from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


# config.py → core → app → backend → enterprise_rag
BASE_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "knowledge-platform"
    env: str = "local"

    database_url: str

    jwt_secret: str

    ollama_base_url: str
    chat_model: str
    embed_model: str
    embed_dim: int

    file_storage_root: str

    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60

    @property
    def file_storage_path(self) -> Path:
        path = Path(self.file_storage_root)
        if not path.is_absolute():
            path = BASE_DIR / path
        return path.resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()