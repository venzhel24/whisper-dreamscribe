# Multi-stage build для оптимизации размера
FROM python:3.11-slim as builder

# Устанавливаем зависимости для сборки
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаем wheel файлы
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/build/wheels -r requirements.txt

# Финальный образ
FROM python:3.11-slim

# Метаданные
LABEL maintainer="your.email@example.com"
LABEL description="Whisper DreamScribe - AI Audio Transcription Service"
LABEL version="1.0.0"

# Устанавливаем runtime зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создаем пользователя
RUN useradd --create-home --shell /bin/bash --uid 1000 whisper

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем wheel файлы и устанавливаем зависимости
COPY --from=builder /build/wheels /tmp/wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --find-links=/tmp/wheels -r requirements.txt \
    && rm -rf /tmp/wheels

# Копируем код приложения
COPY src/ src/
COPY scripts/ scripts/

# Создаем необходимые директории
RUN mkdir -p models logs \
    && chown -R whisper:whisper /app

# Переключаемся на непривилегированного пользователя
USER whisper

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Запуск приложения
CMD ["python", "-m", "src.main"]
