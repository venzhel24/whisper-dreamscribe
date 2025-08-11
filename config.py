import os

class Settings:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    _redis_url_env = os.getenv("REDIS_URL")
    if _redis_url_env:
        REDIS_URL = _redis_url_env
    else:
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    JOBS_QUEUE = os.getenv("JOBS_QUEUE", "transcription_jobs")
    RESULTS_QUEUE = os.getenv("RESULTS_QUEUE", "transcription_results")
    WHISPER_THREADS = int(os.getenv("WHISPER_THREADS", "4"))
    WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "auto")

settings = Settings()

print(f"[CONFIG] REDIS_HOST: {settings.REDIS_HOST}")
print(f"[CONFIG] REDIS_PORT: {settings.REDIS_PORT}")
print(f"[CONFIG] REDIS_URL: {settings.REDIS_URL}")
