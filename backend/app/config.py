import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Podly AI"
    DEBUG: bool = False
    SECRET_KEY: str = "podly-ai-secret-key-change-in-production"

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    OUTPUT_DIR: str = os.path.join(BASE_DIR, "outputs")
    MODEL_CACHE_DIR: str = os.path.join(BASE_DIR, "models")

    # Database
    DATABASE_URL: str = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'podly.db')}"

    # AI Models
    WHISPER_MODEL: str = "tiny"          # tiny, base, small, medium, large
    WHISPER_DEVICE: str = "cpu"          # cpu or cuda
    TRANSCRIPTION_ENGINE: str = "faster-whisper"  # int8 CPU inference; use openai-whisper as fallback
    SUMMARIZER_MODEL: str = "sshleifer/distilbart-cnn-12-6"  # lighter than bart-large
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"               # fast sentence transformer

    # Processing
    MAX_UPLOAD_SIZE_MB: int = 500
    PROCESSING_WORKERS: int = Field(default=1, ge=1, le=8)
    CHUNK_DURATION_SECONDS: int = 30     # whisper chunk size
    MIN_CHAPTER_DURATION_SECONDS: int = 30
    MAX_SUMMARY_INPUT_TOKENS: int = 512
    FAST_PROCESSING: bool = True

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Create required directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
os.makedirs(settings.MODEL_CACHE_DIR, exist_ok=True)
