"""Application configuration settings."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Sheet to Solfa"
    debug: bool = False

    # Storage paths
    upload_dir: Path = Path("./storage/uploads")
    output_dir: Path = Path("./storage/outputs")
    jobs_dir: Path = Path("./storage/jobs")

    # Processing
    pdf_dpi: int = 300
    max_file_size_mb: int = 50

    # API
    api_prefix: str = "/api"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Gemini AI
    gemini_api_key: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()

