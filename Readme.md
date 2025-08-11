# Whisper Worker - AI Audio Transcription Service

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

Сервис для транскрипции аудио с использованием OpenAI Whisper, работающий через Redis очереди.

## 📋 Содержание

- [🚀 Быстрый старт](#-быстрый-старт)
- [⚙️ Конфигурация](#️-конфигурация)
- [🖥️ Системные требования](#️-системные-требования)
- [📊 Производительность](#-производительность)
- [🔧 Разработка](#-разработка)
- [📋 API интеграция](#-api-интеграция)
- [🔍 Мониторинг](#-мониторинг)
- [🐛 Устранение неполадок](#-устранение-неполадок)

## 🚀 Быстрый старт

### Windows 11 (Локальная разработка)

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/your-username/whisper-dreamscribe.git
   cd whisper-dreamscribe
   ```

2. **Запустите скрипт развертывания:**
   
   **Batch скрипт:**
   ```cmd
   deploy-local.bat
   ```
   
   **PowerShell скрипт:**
   ```powershell
   .\deploy-local.ps1
   ```

3. **Следуйте инструкциям в меню** для сборки и запуска сервиса

### Linux/macOS (Production)

1. **Скачайте скрипт развертывания:**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/venzhel24/whisper-dreamscribe/main/deploy.sh | bash
   ```

2. **Или ручная установка:**
   
   **Создание проекта:**
   ```bash
   mkdir -p /projects/whisper-dreamscribe && cd /projects/whisper-dreamscribe
   ```
   
   **Скачивание файлов конфигурации:**
   ```bash
   wget https://raw.githubusercontent.com/venzhel24/whisper-dreamscribe/main/docker-compose.yml
   wget https://raw.githubusercontent.com/venzhel24/whisper-dreamscribe/main/.env.example
   mv .env.example .env
   ```
   
   **Редактирование настроек:**
   ```bash
   nano .env
   ```
   
   **Создание сети:**
   ```bash
   docker network create dreamscribe-network
   ```
   
   **Запуск:**
   ```bash
   docker-compose up -d
   ```

## ⚙️ Конфигурация

### Переменные окружения (.env)

**Redis настройки:**
```env
REDIS_HOST=redis
REDIS_PORT=6379
```

**Whisper настройки:**
```env
WHISPER_MODEL=large-v2  # tiny, base, small, medium, large-v2
WHISPER_THREADS=8       # Количество CPU потоков
WHISPER_LANGUAGE=auto   # auto, ru, en, de, fr, etc.
```

**Очереди:**
```env
JOBS_QUEUE=transcription_jobs      # Очередь входящих задач
RESULTS_QUEUE=transcription_results # Очередь результатов
```

### Модели Whisper

| Модель | Размер | Точность | Скорость | Память |
|--------|--------|----------|----------|---------|
| `tiny` | 39 MB | ~70% | Очень быстро | 1 GB |
| `base` | 142 MB | ~80% | Быстро | 2 GB |  
| `small` | 466 MB | ~85% | Средне | 3 GB |
| `medium` | 1.5 GB | ~90% | Медленно | 4 GB |
| `large-v2` | 2.9 GB | ~95% | Очень медленно | 6 GB |

## 🖥️ Системные требования

### Минимальные требования
- **CPU:** 2+ ядра x86_64 с AVX2
- **RAM:** 4 GB (для small модели)
- **Диск:** 10 GB свободного места
- **OS:** Ubuntu 20.04+, Windows 11, macOS 12+

### Рекомендуемые требования
- **CPU:** 6+ ядер Intel/AMD с высокой одноядерной производительностью
- **RAM:** 8-12 GB (для large-v2 модели)
- **Диск:** 40 GB SSD
- **Сеть:** Стабильное интернет-соединение

### Пропускная способность

- **Последовательная обработка:** 1 аудио файл за раз
- **Параллельная обработка:** Через несколько worker'ов
- **Максимальная нагрузка:** 50-100 пользователей одновременно

## 🔧 Разработка

### Локальная разработка

**Клонирование репозитория:**
```bash
git clone https://github.com/your-username/whisper-dreamscribe.git
cd whisper-dreamscribe
```

**Создание виртуального окружения:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

**Установка зависимостей:**
```bash
pip install -r requirements.txt
```

**Запуск Redis локально:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Запуск worker'а:**
```bash
python main.py
```

### Сборка Docker образа

**Локальная сборка:**
```bash
docker build -t whisper-dreamscribe:latest .
```

**Публикация в Docker Hub:**
```bash
docker build -t your-username/whisper-dreamscribe:latest .
docker push your-username/whisper-dreamscribe:latest
```

**Публикация в GitHub Container Registry:**
```bash
docker build -t ghcr.io/your-username/whisper-dreamscribe:latest .
docker push ghcr.io/your-username/whisper-dreamscribe:latest
```

## 📋 API интеграция

### Добавление задачи в очередь (Node.js)

```javascript
import { Queue } from 'bullmq';

const jobsQueue = new Queue('transcription_jobs', {
  connection: { host: 'localhost', port: 6379 }
});

// Добавление задачи на транскрипцию
await jobsQueue.add('transcribe', {
  userId: 12345,
  messageId: 67890,
  audioUrl: 'https://api.telegram.org/file/bot<token>/voice/file.oga'
});
```

### Получение результатов

```javascript
import { Worker } from 'bullmq';

const resultsWorker = new Worker('transcription_results', async (job) => {
  const { text, userId, messageId } = job.data;
  
  console.log(`Результат для пользователя ${userId}:`, text);
  
  // Обработка результата (отправка пользователю, сохранение в БД, etc.)
}, {
  connection: { host: 'localhost', port: 6379 }
});
```

## 🔍 Мониторинг

### Проверка статуса

**Статус контейнеров:**
```bash
docker-compose ps
```

**Логи всех сервисов:**
```bash
docker-compose logs -f
```

**Логи только whisper-dreamscribe:**
```bash
docker-compose logs -f whisper-dreamscribe
```

**Использование ресурсов:**
```bash
docker stats whisper-dreamscribe
```

### Метрики производительности

**Информация о системе из контейнера:**
```bash
docker-compose exec whisper-dreamscribe python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'RAM: {psutil.virtual_memory().percent}%')
print(f'Диск: {psutil.disk_usage(\"/\").percent}%')
"
```

## 🐛 Устранение неполадок

### Частые проблемы

#### 1. Ошибка подключения к Redis

**Проверка сети Docker:**
```bash
docker network inspect dreamscribe-network
```

**Перезапуск с пересозданием сети:**
```bash
docker-compose down
docker network rm dreamscribe-network
docker network create dreamscribe-network
docker-compose up -d
```

#### 2. Нехватка памяти

**Мониторинг памяти:**
```bash
docker stats whisper-dreamscribe
```

**Уменьшение модели в .env:**
```env
WHISPER_MODEL=medium  # вместо large-v2
```

#### 3. Медленная транскрипция

**Увеличение потоков в .env:**
```env
WHISPER_THREADS=12  # по количеству CPU ядер
```

**Проверка CPU load:**
```bash
docker-compose exec whisper-dreamscribe top
```

### Логи и отладка

**Подробные логи:**
```bash
docker-compose logs -f --tail=100 whisper-dreamscribe
```

**Вход в контейнер для отладки:**
```bash
docker-compose exec whisper-dreamscribe bash
```

**Проверка файлов конфигурации:**
```bash
docker-compose exec whisper-dreamscribe cat .env
```
