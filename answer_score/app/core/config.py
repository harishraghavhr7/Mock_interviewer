from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "mock_interviewer"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = Field(default=False)

    STORAGE_BACKEND: str = Field(default="local")  # local | s3 | sqlite | postgres
    DATA_DIR: Path = Field(default=PROJECT_ROOT / "data")
    TEMP_DIR: Path = Field(default=PROJECT_ROOT / "tmp")

    DATABASE_URL: Optional[str] = None

    STT_PROVIDER: str = Field(default="whisper")  # whisper | google | azure
    WHISPER_MODEL: str = Field(default="small")

    EMBED_MODEL: str = Field(default="all-MiniLM-L6-v2")

    LLM_PROVIDER: str = Field(default="openai")
    OPENAI_API_KEY: Optional[str] = None

    SEMANTIC_WEIGHT: float = Field(default=0.7)
    KEYWORD_WEIGHT: float = Field(default=0.3)
    DEFAULT_QUESTION_WEIGHT: float = Field(default=1.0)
    CRITICAL_QUESTION_WEIGHT: float = Field(default=2.0)

    MAX_AUDIO_SECONDS: int = Field(default=300)
    MAX_FILE_SIZE_MB: int = Field(default=50)

    LOG_LEVEL: str = Field(default="INFO")
    SECRET_KEY: Optional[str] = None

    @property
    def storage_path(self) -> Path:
        return Path(self.DATA_DIR)

    def ensure_dirs(self) -> None:
        for p in (self.DATA_DIR, self.TEMP_DIR):
            Path(p).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()

__all__ = ["settings", "Settings", "PROJECT_ROOT"]