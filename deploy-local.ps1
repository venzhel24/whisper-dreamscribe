# PowerShell скрипт для развертывания whisper-dreamscribe

param(
    [Parameter()]
    [ValidateSet("build", "run", "clean", "stop", "logs", "push")]
    [string]$Action = "menu"
)

function Show-Banner {
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "🚀 Локальное развертывание whisper-dreamscribe" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-DockerInstallation {
    try {
        $null = Get-Command docker -ErrorAction Stop
        $null = Get-Command docker-compose -ErrorAction Stop
        Write-Host "✅ Docker найден" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Docker или Docker Compose не найдены!" -ForegroundColor Red
        Write-Host "Установите Docker Desktop для Windows" -ForegroundColor Yellow
        return $false
    }
}

function Initialize-Environment {
    # Создание .env файла
    if (!(Test-Path ".env")) {
        Write-Host "📝 Создание .env файла..." -ForegroundColor Yellow
        @"
REDIS_HOST=redis
REDIS_PORT=6379
WHISPER_MODEL=large-v2
JOBS_QUEUE=transcription_jobs
RESULTS_QUEUE=transcription_results
WHISPER_THREADS=8
WHISPER_LANGUAGE=auto
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Host "✅ Файл .env создан" -ForegroundColor Green
    }

    # Создание директории логов
    if (!(Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" | Out-Null
        Write-Host "✅ Директория логов создана" -ForegroundColor Green
    }

    # Создание Docker сети
    $networkExists = docker network ls --format "{{.Name}}" | Where-Object { $_ -eq "dreamscribe-network" }
    if (!$networkExists) {
        Write-Host "🌐 Создание Docker сети..." -ForegroundColor Yellow
        docker network create dreamscribe-network | Out-Null
        Write-Host "✅ Сеть dreamscribe-network создана" -ForegroundColor Green
    }
}

function Show-Menu {
    Write-Host "Выберите действие:" -ForegroundColor Cyan
    Write-Host "1. Собрать образ локально и запустить" -ForegroundColor White
    Write-Host "2. Только запустить (без пересборки)" -ForegroundColor White
    Write-Host "3. Пересобрать и запустить с очисткой кэша" -ForegroundColor White
    Write-Host "4. Остановить сервисы" -ForegroundColor White
    Write-Host "5. Посмотреть логи" -ForegroundColor White
    Write-Host "6. Опубликовать образ в Docker Hub" -ForegroundColor White
    Write-Host ""
}

function Build-And-Run {
    Write-Host "🔨 Сборка образа..." -ForegroundColor Yellow
    docker-compose build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Ошибка сборки образа" -ForegroundColor Red
        return $false
    }
    Write-Host "✅ Образ собран" -ForegroundColor Green
    Start-Services
}

function Start-Services {
    Write-Host "🟢 Запуск сервисов..." -ForegroundColor Yellow
    docker-compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Ошибка запуска сервисов" -ForegroundColor Red
        return $false
    }

    Write-Host ""
    Write-Host "✅ Сервисы запущены!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Полезные команды:" -ForegroundColor Cyan
    Write-Host "   docker-compose ps                    - статус контейнеров" -ForegroundColor White
    Write-Host "   docker-compose logs -f               - логи всех сервисов" -ForegroundColor White
    Write-Host "   docker-compose logs -f whisper-dreamscribe - логи whisper-dreamscribe" -ForegroundColor White
    Write-Host "   docker-compose stop                  - остановка сервисов" -ForegroundColor White
    Write-Host "   docker-compose down                  - остановка и удаление контейнеров" -ForegroundColor White
}

function Clean-Build {
    Write-Host "🧹 Очистка кэша Docker..." -ForegroundColor Yellow
    docker system prune -f | Out-Null
    Write-Host "🔨 Сборка образа без кэша..." -ForegroundColor Yellow
    docker-compose build --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Ошибка сборки образа" -ForegroundColor Red
        return $false
    }
    Write-Host "✅ Образ пересобран" -ForegroundColor Green
    Start-Services
}

function Stop-Services {
    Write-Host "🛑 Остановка сервисов..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✅ Сервисы остановлены" -ForegroundColor Green
}

function Show-Logs {
    Write-Host "📋 Показ логов whisper-dreamscribe (Ctrl+C для выхода)..." -ForegroundColor Yellow
    docker-compose logs -f whisper-dreamscribe
}

function Push-Image {
    $registry = Read-Host "Введите ваш Docker Hub username"
    if ([string]::IsNullOrEmpty($registry)) {
        Write-Host "❌ Username не может быть пустым" -ForegroundColor Red
        return $false
    }

    Write-Host "🔨 Сборка образа для публикации..." -ForegroundColor Yellow
    docker build -t "$registry/whisper-dreamscribe:latest" .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Ошибка сборки образа" -ForegroundColor Red
        return $false
    }

    Write-Host "🔐 Выполните вход в Docker Hub..." -ForegroundColor Yellow
    docker login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Ошибка авторизации" -ForegroundColor Red
        return $false
    }

    Write-Host "📤 Отправка образа..." -ForegroundColor Yellow
    docker push "$registry/whisper-dreamscribe:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Ошибка отправки образа" -ForegroundColor Red
        return $false
    }

    Write-Host "✅ Образ опубликован: $registry/whisper-dreamscribe:latest" -ForegroundColor Green
}

# Основная логика
Show-Banner

if (!(Test-DockerInstallation)) {
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Initialize-Environment

if ($Action -eq "menu") {
    Show-Menu
    $choice = Read-Host "Введите номер (1-6)"
    
    switch ($choice) {
        "1" { Build-And-Run }
        "2" { Start-Services }
        "3" { Clean-Build }
        "4" { Stop-Services }
        "5" { Show-Logs }
        "6" { Push-Image }
        default { 
            Write-Host "❌ Неверный выбор" -ForegroundColor Red
            Read-Host "Нажмите Enter для выхода"
            exit 1
        }
    }
} else {
    switch ($Action) {
        "build" { Build-And-Run }
        "run" { Start-Services }
        "clean" { Clean-Build }
        "stop" { Stop-Services }
        "logs" { Show-Logs }
        "push" { Push-Image }
    }
}

Read-Host "Нажмите Enter для выхода"
