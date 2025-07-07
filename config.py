import os

class Settings:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v2")
    JOBS_QUEUE = os.getenv("JOBS_QUEUE", "transcription_jobs")
    RESULTS_QUEUE = os.getenv("RESULTS_QUEUE", "transcription_results")

settings = Settings()
