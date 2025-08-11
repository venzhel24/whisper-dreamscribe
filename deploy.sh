#!/bin/bash

set -e

echo "🚀 Развертывание whisper-worker..."

mkdir -p /opt/whisper-worker
cd /opt/whisper-worker

if [ ! -f docker-compose.yml ]; then
    echo "📥 Скачивание docker-compose.yml..."
    wget -O docker-compose.yml https://raw.githubusercontent.com/venzhel24/whisper-dreamscribe/main/docker-compose.yml
fi

if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cat > .env << EOF
REDIS_HOST=redis
REDIS_PORT=6379
WHISPER_MODEL=large-v2
JOBS_QUEUE=transcription_jobs
RESULTS_QUEUE=transcription_results
WHISPER_THREADS=8
WHISPER_LANGUAGE=auto
EOF
    echo "⚠️  Отредактируйте .env файл под ваши нужды"
fi

if ! docker network ls | grep -q dreamscribe-network; then
    echo "🌐 Создание Docker сети..."
    docker network create dreamscribe-network
fi

mkdir -p logs

echo "⬇️  Скачивание образа..."
docker-compose pull

echo "🟢 Запуск сервиса..."
docker-compose up -d

echo "✅ Развертывание завершено!"
echo "📋 Проверить статус: docker-compose ps"
echo "📋 Посмотреть логи: docker-compose logs -f whisper-worker"
