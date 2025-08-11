"""Основной модуль worker'а для транскрипции аудио."""

import asyncio
import signal
import time
from typing import Any, Dict

from loguru import logger

from .config import settings
from .models.whisper_model import model_manager
from .services.audio_service import AudioService
from .services.queue_service import queue_service
from .utils.logger import setup_logger


class TranscriptionWorker:
    """Worker для транскрипции аудио."""

    def __init__(self):
        self.model = model_manager.get_model()
        self.audio_service = AudioService()
        self.shutdown_event = asyncio.Event()

    async def process_job(self, job, job_token) -> Dict[str, Any]:
        """Обрабатывает задачу транскрипции."""
        data = job.data
        user_id = data.get('userId')
        message_id = data.get('messageId')
        audio_url = data.get('audioUrl')

        logger.info(f"Получена задача: userId={user_id}, messageId={message_id}")

        audio_path = None
        wav_path = None

        try:
            # Скачивание и конвертация аудио
            audio_path = await self.audio_service.download_audio(audio_url)
            wav_path = await self.audio_service.convert_to_wav(audio_path)

            # Транскрипция
            text = await self._transcribe_audio(wav_path)
            logger.info(f"Транскрипция завершена. Длина текста: {len(text)}")

            # Формирование результата
            result = {
                'text': text,
                'userId': user_id,
                'messageId': message_id
            }

            # Отправка результата
            await queue_service.send_result(result)
            return result

        except Exception as e:
            logger.error(f"Ошибка обработки задачи: {e}")
            return {
                'error': str(e),
                'userId': user_id,
                'messageId': message_id
            }
        finally:
            # Очистка временных файлов
            if audio_path or wav_path:
                self.audio_service.cleanup_files(audio_path, wav_path)

    async def _transcribe_audio(self, wav_path: str) -> str:
        """Выполняет транскрипцию аудио файла."""
        logger.debug(f"Начинается транскрипция файла {wav_path}")
        start_time = time.time()

        loop = asyncio.get_event_loop()

        def transcribe_sync():
            segments, info = self.model.transcribe(
                wav_path,
                language=None if settings.whisper_language == "auto" else settings.whisper_language,
                beam_size=1,
                best_of=1,
                temperature=0.0,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,
                condition_on_previous_text=False
            )

            text = "".join([segment.text for segment in segments])
            return text, info

        text, info = await loop.run_in_executor(None, transcribe_sync)
        end_time = time.time()

        logger.info(
            f"Транскрипция завершена за {end_time - start_time:.2f}с. "
            f"Язык: {info.language} ({info.language_probability:.1%})"
        )

        return text

    def _setup_signal_handlers(self) -> None:
        """Настраивает обработчики сигналов."""
        def signal_handler(*_):
            logger.warning("Получен сигнал завершения, останавливаем worker...")
            self.shutdown_event.set()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def run(self) -> None:
        """Запускает worker."""
        logger.info(f"Запуск worker для очереди {settings.jobs_queue}")
        logger.info(f"Redis подключение: {settings.redis_connection_url}")

        self._setup_signal_handlers()

        worker = queue_service.create_worker(self.process_job)

        logger.success("Worker запущен и ожидает задачи...")

        try:
            await self.shutdown_event.wait()
        finally:
            logger.info("Завершение работы worker...")
            await worker.close()
            logger.success("Worker остановлен")


async def main() -> None:
    """Главная функция."""
    setup_logger()
    logger.info("Запуск whisper-dreamscribe worker")

    try:
        worker = TranscriptionWorker()
        await worker.run()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
