"""Конфигурация приложения с использованием Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    # Redis настройки
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_url: str = Field(default="", description="Full Redis URL")

    # Whisper настройки
    whisper_model: str = Field(default="large-v2", description="Whisper model name")
    whisper_threads: int = Field(default=8, description="Number of CPU threads")
    whisper_language: str = Field(default="auto", description="Audio language")

    # Очереди
    jobs_queue: str = Field(default="transcription_jobs", description="Input jobs queue")
    results_queue: str = Field(default="transcription_results", description="Results queue")

    # Логирование
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        description="Log format"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def redis_connection_url(self) -> str:
        """Возвращает URL для подключения к Redis."""
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}"


settings = Settings()
