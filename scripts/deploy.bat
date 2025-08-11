@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ===============================================
echo 🚀 Whisper DreamScribe Manager для Windows
echo ===============================================

:: Проверка зависимостей
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

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)

echo ✅ Все зависимости найдены

:: Настройка проекта
if not exist models mkdir models
if not exist logs mkdir logs
echo ✅ Директории созданы

:: Создание .env файла
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
        echo LOG_LEVEL=INFO
    ) > .env
    echo ✅ .env файл создан
)

:: Создание Docker сети
docker network ls | findstr dreamscribe-network >nul
if %errorlevel% neq 0 (
    echo 🌐 Создание Docker сети...
    docker network create dreamscribe-network
    echo ✅ Сеть dreamscribe-network создана
)

:menu
cls
echo ===============================================
echo 🚀 Whisper DreamScribe Manager
echo ===============================================
echo.
echo 1. 📥 Скачать модель
echo 2. 🔨 Собрать и запустить
echo 3. ▶️  Запустить (без пересборки^)
echo 4. 🧹 Полная пересборка
echo 5. 🛑 Остановить сервисы
echo 6. 📋 Показать логи
echo 7. 📊 Статус сервисов
echo 8. 🧽 Очистить систему
echo 9. 📤 Опубликовать образ в Docker Hub
echo 0. 🚪 Выход
echo.
set /p choice="Выберите действие (0-9): "

if "%choice%"=="1" goto download_model
if "%choice%"=="2" goto build_and_run
if "%choice%"=="3" goto start_services
if "%choice%"=="4" goto full_rebuild
if "%choice%"=="5" goto stop_services
if "%choice%"=="6" goto show_logs
if "%choice%"=="7" goto show_status
if "%choice%"=="8" goto cleanup_system
if "%choice%"=="9" goto push_image
if "%choice%"=="0" goto exit
goto invalid_choice

:download_model
echo 📥 Скачивание модели...
python scripts\download-model.py
if %errorlevel% neq 0 (
    echo ❌ Ошибка скачивания модели
    pause
    goto menu
)
echo ✅ Модель скачана успешно
pause
goto menu

:build_and_run
echo 🔨 Сборка образа...
docker-compose -f docker\docker-compose.yml build
if %errorlevel% neq 0 (
    echo ❌ Ошибка сборки образа
    pause
    goto menu
)
echo ✅ Образ собран
goto start_services

:start_services
echo 🟢 Запуск сервисов...
docker-compose -f docker\docker-compose.yml up -d
if %errorlevel% neq 0 (
    echo ❌ Ошибка запуска сервисов
    pause
    goto menu
)
echo.
echo ✅ Сервисы запущены!
call :show_useful_commands
pause
goto menu

:full_rebuild
echo 🧹 Полная пересборка системы...
docker-compose -f docker\docker-compose.yml down
docker system prune -f
docker-compose -f docker\docker-compose.yml build --no-cache
if %errorlevel% neq 0 (
    echo ❌ Ошибка пересборки
    pause
    goto menu
)
goto start_services

:stop_services
echo 🛑 Остановка сервисов...
docker-compose -f docker\docker-compose.yml down
echo ✅ Сервисы остановлены
pause
goto menu

:show_logs
echo 📋 Показ логов (Ctrl+C для выхода)...
docker-compose -f docker\docker-compose.yml logs -f whisper-dreamscribe
pause
goto menu

:show_status
echo 📊 Статус сервисов:
docker-compose -f docker\docker-compose.yml ps
echo.
echo 📊 Использование ресурсов:
docker stats whisper-dreamscribe --no-stream 2>nul || echo ⚠️  Контейнер не запущен
pause
goto menu

:cleanup_system
echo ⚠️  Очистка системы Docker...
echo Это удалит все неиспользуемые образы, контейнеры и volumes!
set /p confirm="Вы уверены? (y/N): "
if /i not "%confirm%"=="y" goto menu

docker-compose -f docker\docker-compose.yml down
docker system prune -a -f
docker volume prune -f
echo ✅ Система очищена
pause
goto menu

:push_image
echo 📤 Публикация образа в Docker Hub...
set /p registry="Введите ваш Docker Hub username: "
if "%registry%"=="" (
    echo ❌ Username не может быть пустым
    pause
    goto menu
)

echo 🔨 Сборка образа для публикации...
docker build -f docker\Dockerfile -t %registry%/whisper-dreamscribe:latest .
if %errorlevel% neq 0 (
    echo ❌ Ошибка сборки образа
    pause
    goto menu
)

echo 🔐 Вход в Docker Hub...
docker login
if %errorlevel% neq 0 (
    echo ❌ Ошибка авторизации
    pause
    goto menu
)

echo 📤 Отправка образа...
docker push %registry%/whisper-dreamscribe:latest
if %errorlevel% neq 0 (
    echo ❌ Ошибка отправки образа
    pause
    goto menu
)

echo ✅ Образ опубликован: %registry%/whisper-dreamscribe:latest
pause
goto menu

:show_useful_commands
echo 📋 Полезные команды:
echo    docker-compose -f docker\docker-compose.yml ps           - статус контейнеров
echo    docker-compose -f docker\docker-compose.yml logs -f      - логи всех сервисов
echo    docker-compose -f docker\docker-compose.yml stop         - остановка сервисов
echo    docker stats whisper-dreamscribe                        - мониторинг ресурсов
echo.
goto :eof

:invalid_choice
echo ❌ Неверный выбор. Попробуйте снова.
pause
goto menu

:exit
echo 👋 До свидания!
pause
exit /b 0
