@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ===============================================
echo 🚀 Локальное развертывание whisper-dreamscribe
echo ===============================================

:: Проверка наличия Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker не найден! Установите Docker Desktop
    pause
    exit /b 1
)

where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker Compose не найден! Обновите Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker найден

:: Создание .env файла если не существует
if not exist .env (
    echo 📝 Создание .env файла...
    (
        echo REDIS_HOST=redis
        echo REDIS_PORT=6379
        echo WHISPER_MODEL=large-v2
        echo JOBS_QUEUE=transcription_jobs
        echo RESULTS_QUEUE=transcription_results
        echo WHISPER_THREADS=8
        echo WHISPER_LANGUAGE=auto
    ) > .env
    echo ✅ Файл .env создан
)

:: Создание директорий
if not exist logs mkdir logs
if not exist models mkdir models
echo ✅ Директории созданы

:: Создание внешней сети если не существует
docker network ls | findstr dreamscribe-network >nul
if %errorlevel% neq 0 (
    echo 🌐 Создание Docker сети...
    docker network create dreamscribe-network
    echo ✅ Сеть dreamscribe-network создана
)

:: Выбор действия
echo.
echo Выберите действие:
echo 1. Скачать модель из .env файла
echo 2. Собрать образ и запустить
echo 3. Только запустить (без пересборки)
echo 4. Пересобрать и запустить с очисткой кэша
echo 5. Остановить сервисы
echo 6. Посмотреть логи
echo 7. Опубликовать образ в Docker Hub
echo.
set /p choice="Введите номер (1-7): "

if "%choice%"=="1" goto download_model
if "%choice%"=="2" goto build_and_run
if "%choice%"=="3" goto run_only
if "%choice%"=="4" goto clean_build
if "%choice%"=="5" goto stop_services
if "%choice%"=="6" goto show_logs
if "%choice%"=="7" goto push_image
goto invalid_choice

:download_model
echo 📥 Скачивание модели...
python download-model.py
if %errorlevel% neq 0 (
    echo ❌ Ошибка скачивания модели
    pause
    exit /b 1
)
echo ✅ Модель скачана
pause
exit /b 0

:build_and_run
echo 🔨 Сборка образа...
docker-compose build
if %errorlevel% neq 0 (
    echo ❌ Ошибка сборки образа
    pause
    exit /b 1
)
echo ✅ Образ собран
goto start_services

:run_only
echo ▶️  Запуск без пересборки...
goto start_services

:clean_build
echo 🧹 Очистка кэша Docker...
docker system prune -f
echo 🔨 Сборка образа без кэша...
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo ❌ Ошибка сборки образа
    pause
    exit /b 1
)
echo ✅ Образ пересобран
goto start_services

:start_services
echo 🟢 Запуск сервисов...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ Ошибка запуска сервисов
    pause
    exit /b 1
)

echo.
echo ✅ Сервисы запущены!
echo.
echo 📋 Полезные команды:
echo    docker-compose ps                         - статус контейнеров
echo    docker-compose logs -f                    - логи всех сервисов
echo    docker-compose logs -f whisper-dreamscribe - логи whisper-dreamscribe
echo    docker-compose stop                       - остановка сервисов
echo    docker-compose down                       - остановка и удаление контейнеров
echo.
pause
exit /b 0

:stop_services
echo 🛑 Остановка сервисов...
docker-compose down
echo ✅ Сервисы остановлены
pause
exit /b 0

:show_logs
echo 📋 Показ логов whisper-dreamscribe (Ctrl+C для выхода)...
docker-compose logs -f whisper-dreamscribe
pause
exit /b 0

:push_image
echo 📤 Публикация образа в Docker Hub...
set /p registry="Введите ваш Docker Hub username: "
if "%registry%"=="" (
    echo ❌ Username не может быть пустым
    pause
    exit /b 1
)

echo 🔨 Сборка образа для публикации...
docker build -t %registry%/whisper-dreamscribe:latest .
if %errorlevel% neq 0 (
    echo ❌ Ошибка сборки образа
    pause
    exit /b 1
)

echo 🔐 Выполните вход в Docker Hub...
docker login
if %errorlevel% neq 0 (
    echo ❌ Ошибка авторизации
    pause
    exit /b 1
)

echo 📤 Отправка образа...
docker push %registry%/whisper-dreamscribe:latest
if %errorlevel% neq 0 (
    echo ❌ Ошибка отправки образа
    pause
    exit /b 1
)

echo ✅ Образ опубликован: %registry%/whisper-dreamscribe:latest
pause
exit /b 0

:invalid_choice
echo ❌ Неверный выбор
pause
exit /b 1
