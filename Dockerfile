# Используем slim образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash whisper

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt для лучшего кэширования слоев
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY main.py config.py ./

# Создаем директории
RUN mkdir -p /app/models /app/logs

# Меняем владельца файлов
RUN chown -R whisper:whisper /app

# Переключаемся на непривилегированного пользователя
USER whisper

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Запускаем приложение
CMD ["python", "main.py"]
