import asyncio
from bullmq import Worker, Queue
from config import settings
import aiohttp
import tempfile
import os
import traceback
import torch
from faster_whisper import WhisperModel

print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

print(f"[START] Загрузка модели Faster-Whisper: {settings.WHISPER_MODEL}")
try:
    # faster-whisper использует WhisperModel вместо whisper.load_model
    model = WhisperModel(settings.WHISPER_MODEL, device="cuda", compute_type="float16")
    print("[READY] Модель Faster-Whisper загружена")
except Exception as e:
    print(f"[FATAL] Не удалось загрузить модель Faster-Whisper: {e}")
    raise

async def download_audio(url: str) -> str:
    print(f"[DOWNLOAD] Скачивание аудио из {url}")
    connector = aiohttp.TCPConnector(ssl=False)
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f"[ERROR] Не удалось скачать аудио: статус {resp.status}")
                    raise Exception(f"Failed to download audio: {resp.status}")
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.oga')
                content = await resp.read()
                tmp_file.write(content)
                tmp_file.close()
                print(f"[DOWNLOAD] Файл сохранён во временный путь {tmp_file.name}")
                return tmp_file.name
    except Exception as e:
        print(f"[ERROR] Ошибка при скачивании аудио: {e}")
        traceback.print_exc()
        raise

async def convert_to_wav_async(input_path: str) -> str:
    output_path = input_path.rsplit('.', 1)[0] + ".wav"
    print(f"[CONVERT] Конвертация {input_path} в {output_path} через ffmpeg (async)")
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", input_path, output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"[ERROR] Ошибка ffmpeg: {stderr.decode()}")
            raise Exception(f"ffmpeg failed: {stderr.decode()}")
        print(f"[CONVERT] Конвертация завершена: {output_path}")
        return output_path
    except Exception as e:
        print(f"[ERROR] Ошибка при конвертации аудио: {e}")
        traceback.print_exc()
        raise

async def process(job, job_token):
    data = job.data
    print(f"[QUEUE] Получена задача: userId={data.get('userId')}, messageId={data.get('messageId')}, audioUrl={data.get('audioUrl')}")
    audio_path = None
    wav_path = None
    try:
        # Скачивание аудио
        audio_path = await download_audio(data['audioUrl'])

        # Конвертация в wav
        wav_path = await convert_to_wav_async(audio_path)

        # Транскрипция с faster-whisper
        print(f"[WHISPER] Начинается транскрипция файла {wav_path}")
        loop = asyncio.get_event_loop()

        # faster-whisper возвращает кортеж (segments, info)
        def transcribe_sync():
            segments, info = model.transcribe(wav_path)
            # Собираем текст из всех сегментов
            text = "".join([segment.text for segment in segments])
            return text

        text = await loop.run_in_executor(None, transcribe_sync)
        print(f"[WHISPER] Транскрипция завершена. Текст:\n{text}\n")

        transcription_result = {
            'text': text,
            'userId': data['userId'],
            'messageId': data['messageId']
        }

        # Отправка результата в очередь
        print(f"[QUEUE] Отправка результата в очередь {settings.RESULTS_QUEUE}")
        result_queue = Queue(settings.RESULTS_QUEUE)
        await result_queue.add("result", transcription_result)
        await result_queue.close()
        print(f"[QUEUE] Результат отправлен для userId={data['userId']}, messageId={data['messageId']}")
        return transcription_result

    except Exception as e:
        print(f"[FAIL] Ошибка обработки задачи: {e}")
        traceback.print_exc()
        return {'error': str(e), 'userId': data.get('userId'), 'messageId': data.get('messageId')}
    finally:
        for f in (audio_path, wav_path):
            if f and os.path.exists(f):
                try:
                    os.unlink(f)
                    print(f"[CLEANUP] Временный файл удалён: {f}")
                except Exception as e:
                    print(f"[CLEANUP] Не удалось удалить файл {f}: {e}")

async def main():
    print(f"[INIT] Запуск воркера для очереди {settings.JOBS_QUEUE} (Redis: {settings.REDIS_URL})")

    shutdown_event = asyncio.Event()

    def signal_handler(*_):
        print("[SHUTDOWN] Получен сигнал завершения, останавливаем воркер...")
        shutdown_event.set()

    import signal
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    worker = Worker(
        settings.JOBS_QUEUE,
        process,
        {"connection": settings.REDIS_URL}
    )

    print("[WORKER] Воркер запущен и ожидает задачи...")
    await shutdown_event.wait()
    print("[WORKER] Завершение работы воркера...")
    await worker.close()
    print("[WORKER] Воркер остановлен.")

if __name__ == "__main__":
    print("[SYSTEM] Запуск whisper-worker")
    asyncio.run(main())
