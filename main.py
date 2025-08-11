import asyncio
from bullmq import Worker, Queue
from config import settings
import aiohttp
import tempfile
import os
import traceback
import time
from faster_whisper import WhisperModel
from pathlib import Path

print(f"[START] Загрузка модели Faster-Whisper: {settings.WHISPER_MODEL}")

def find_local_model(model_name: str) -> Path:
    """Ищет модель в локальных папках"""
    possible_paths = [
        Path(f"./models/{model_name}"),                              # Простое имя
        Path(f"/app/models/{model_name}"),                           # Простое имя в контейнере
        Path(f"./models/models--Systran--faster-whisper-{model_name}"),  # HuggingFace формат
        Path(f"/app/models/models--Systran--faster-whisper-{model_name}"), # HuggingFace в контейнере
        Path(f"./whisper_cache"),                                    # Старый формат кэша
        Path(f"/app/whisper_cache"),                                 # Старый формат в контейнере
    ]

    for path in possible_paths:
        if path.exists() and any(path.iterdir() if path.is_dir() else []):
            print(f"[MODEL] Найдена локальная модель: {path}")
            return path

    return None

def load_whisper_model():
    """Загружает модель Whisper с поиском локальной версии"""
    model_name = settings.WHISPER_MODEL

    # 1. Ищем локальную модель
    local_model_path = find_local_model(model_name)

    if local_model_path:
        try:
            print(f"[MODEL] Попытка загрузки локальной модели из: {local_model_path}")

            # Устанавливаем путь к кэшу
            cache_dir = local_model_path.parent
            os.environ['HF_HOME'] = str(cache_dir)
            os.environ['TRANSFORMERS_CACHE'] = str(cache_dir)

            model = WhisperModel(
                model_name,
                device="cpu",
                compute_type="int8",
                cpu_threads=8,
                num_workers=2,
                download_root=str(cache_dir)
            )

            print(f"[READY] Модель {model_name} загружена из локального кэша")
            return model

        except Exception as e:
            print(f"[WARNING] Ошибка загрузки локальной модели: {e}")
            print(f"[INFO] Переход к автоматическому скачиванию...")

    # 2. Автоматическое скачивание если локальная модель не найдена
    try:
        print(f"[MODEL] Автоматическое скачивание модели {model_name}...")

        # Создаем папку для моделей в контейнере
        models_dir = Path("/app/models")
        models_dir.mkdir(parents=True, exist_ok=True)

        os.environ['HF_HOME'] = str(models_dir)
        os.environ['TRANSFORMERS_CACHE'] = str(models_dir)

        model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
            cpu_threads=8,
            num_workers=2,
            download_root=str(models_dir)
        )

        print(f"[READY] Модель {model_name} загружена через автоскачивание")
        return model

    except Exception as e:
        raise Exception(f"Не удалось загрузить модель {model_name}: {e}")

# Загружаем модель
try:
    model = load_whisper_model()
except Exception as e:
    print(f"[FATAL] Не удалось загрузить модель: {e}")
    raise

REDIS_CONNECTION_CONFIG = {"connection": settings.REDIS_URL}

# Остальной код остается без изменений...
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
            "ffmpeg", "-y", "-i", input_path,
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            output_path,
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

async def transcribe_with_faster_whisper(wav_path: str) -> str:
    print(f"[WHISPER] Начинается транскрипция файла {wav_path}")
    start_time = time.time()

    loop = asyncio.get_event_loop()

    def transcribe_sync():
        segments, info = model.transcribe(
            wav_path,
            language=None if settings.WHISPER_LANGUAGE == "auto" else settings.WHISPER_LANGUAGE,
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

    print(f"[WHISPER] Время обработки: {end_time - start_time:.2f} секунд")
    print(f"[WHISPER] Определенный язык: {info.language} (вероятность: {info.language_probability:.2%})")
    print(f"[WHISPER] Транскрипция завершена")
    return text

async def process(job, job_token):
    data = job.data
    print(f"[QUEUE] Получена задача: userId={data.get('userId')}, messageId={data.get('messageId')}, audioUrl={data.get('audioUrl')}")
    audio_path = None
    wav_path = None
    try:
        audio_path = await download_audio(data['audioUrl'])
        wav_path = await convert_to_wav_async(audio_path)
        text = await transcribe_with_faster_whisper(wav_path)
        print(f"[WHISPER] Транскрипция завершена. Текст:\n{text}\n")

        transcription_result = {
            'text': text,
            'userId': data['userId'],
            'messageId': data['messageId']
        }

        print(f"[QUEUE] Отправка результата в очередь {settings.RESULTS_QUEUE}")
        try:
            result_queue = Queue(settings.RESULTS_QUEUE, REDIS_CONNECTION_CONFIG)
            await result_queue.add("result", transcription_result)
            await result_queue.close()
            print(f"[QUEUE] Результат успешно отправлен для userId={data['userId']}, messageId={data['messageId']}")
        except Exception as redis_error:
            print(f"[ERROR] Ошибка отправки в Redis: {redis_error}")
            raise

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
        REDIS_CONNECTION_CONFIG
    )

    print("[WORKER] Воркер запущен и ожидает задачи...")
    await shutdown_event.wait()
    print("[WORKER] Завершение работы воркера...")
    await worker.close()
    print("[WORKER] Воркер остановлен.")

if __name__ == "__main__":
    print("[SYSTEM] Запуск whisper-worker с faster-whisper")
    asyncio.run(main())
