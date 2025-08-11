"""Сервис для работы с аудио файлами."""

import asyncio
import tempfile
from pathlib import Path
from typing import Tuple

import aiohttp
from loguru import logger


class AudioService:
    """Сервис для работы с аудио."""

    @staticmethod
    async def download_audio(url: str) -> str:
        """Скачивает аудио файл."""
        logger.info(f"Скачивание аудио из {url}")

        connector = aiohttp.TCPConnector(ssl=False)
        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        raise ValueError(f"Не удалось скачать аудио: статус {resp.status}")

                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.oga')
                    content = await resp.read()
                    tmp_file.write(content)
                    tmp_file.close()

                    logger.debug(f"Файл сохранён в {tmp_file.name}")
                    return tmp_file.name

        except Exception as e:
            logger.error(f"Ошибка скачивания аудио: {e}")
            raise

    @staticmethod
    async def convert_to_wav(input_path: str) -> str:
        """Конвертирует аудио в WAV формат."""
        output_path = input_path.rsplit('.', 1)[0] + ".wav"
        logger.debug(f"Конвертация {input_path} в {output_path}")

        try:
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-i", input_path,
                "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
                output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                raise RuntimeError(f"FFmpeg ошибка: {stderr.decode()}")

            logger.debug(f"Конвертация завершена: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Ошибка конвертации аудио: {e}")
            raise

    @staticmethod
    def cleanup_files(*file_paths: str) -> None:
        """Удаляет временные файлы."""
        for file_path in file_paths:
            if file_path and Path(file_path).exists():
                try:
                    Path(file_path).unlink()
                    logger.debug(f"Удалён временный файл: {file_path}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить файл {file_path}: {e}")
