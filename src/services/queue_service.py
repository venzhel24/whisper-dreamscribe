"""Сервис для работы с очередями Redis."""

from typing import Any, Dict

from bullmq import Queue, Worker
from loguru import logger

from ..config import settings


class QueueService:
    """Сервис для работы с очередями."""

    def __init__(self):
        self.redis_config = {"connection": settings.redis_connection_url}

    async def send_result(self, result: Dict[str, Any]) -> None:
        """Отправляет результат в очередь результатов."""
        logger.info(f"Отправка результата в очередь {settings.results_queue}")

        try:
            result_queue = Queue(settings.results_queue, self.redis_config)
            await result_queue.add("result", result)
            await result_queue.close()

            logger.success(f"Результат отправлен для userId={result.get('userId')}")

        except Exception as e:
            logger.error(f"Ошибка отправки в Redis: {e}")
            raise

    def create_worker(self, process_function) -> Worker:
        """Создаёт worker для обработки задач."""
        return Worker(settings.jobs_queue, process_function, self.redis_config)


queue_service = QueueService()
