"""Управление моделями Whisper."""

import os
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel
from loguru import logger

from ..config import settings


class WhisperModelManager:
    """Менеджер моделей Whisper."""

    def __init__(self):
        self.model: Optional[WhisperModel] = None
        self._model_paths = [
            Path(f"./models/{settings.whisper_model}"),
            Path(f"/app/models/{settings.whisper_model}"),
            Path(f"./models/models--Systran--faster-whisper-{settings.whisper_model}"),
            Path(f"/app/models/models--Systran--faster-whisper-{settings.whisper_model}"),
        ]

    def find_local_model(self) -> Optional[Path]:
        """Ищет локальную модель."""
        for path in self._model_paths:
            if path.exists() and any(path.iterdir() if path.is_dir() else []):
                logger.info(f"Найдена локальная модель: {path}")
                return path
        return None

    def load_model(self) -> WhisperModel:
        """Загружает модель Whisper."""
        logger.info(f"Загрузка модели Faster-Whisper: {settings.whisper_model}")

        # Поиск локальной модели
        local_path = self.find_local_model()

        if local_path:
            try:
                logger.info(f"Загрузка локальной модели из: {local_path}")
                cache_dir = local_path.parent
                self._set_cache_env(cache_dir)

                self.model = WhisperModel(
                    settings.whisper_model,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=settings.whisper_threads,
                    num_workers=2,
                    download_root=str(cache_dir)
                )

                logger.success(f"Модель {settings.whisper_model} загружена из локального кэша")
                return self.model

            except Exception as e:
                logger.warning(f"Ошибка загрузки локальной модели: {e}")
                logger.info("Переход к автоматическому скачиванию...")

        # Автоматическое скачивание
        try:
            logger.info(f"Автоматическое скачивание модели {settings.whisper_model}")

            models_dir = Path("/app/models")
            models_dir.mkdir(parents=True, exist_ok=True)
            self._set_cache_env(models_dir)

            self.model = WhisperModel(
                settings.whisper_model,
                device="cpu",
                compute_type="int8",
                cpu_threads=settings.whisper_threads,
                num_workers=2,
                download_root=str(models_dir)
            )

            logger.success(f"Модель {settings.whisper_model} загружена через автоскачивание")
            return self.model

        except Exception as e:
            raise RuntimeError(f"Не удалось загрузить модель {settings.whisper_model}: {e}")

    def _set_cache_env(self, cache_dir: Path) -> None:
        """Устанавливает переменные окружения для кэша."""
        os.environ['HF_HOME'] = str(cache_dir)
        os.environ['TRANSFORMERS_CACHE'] = str(cache_dir)

    def get_model(self) -> WhisperModel:
        """Возвращает загруженную модель."""
        if self.model is None:
            self.model = self.load_model()
        return self.model


# Глобальный экземпляр менеджера
model_manager = WhisperModelManager()
