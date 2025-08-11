#!/bin/bash

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Функции для цветного вывода
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Определение ОС
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker не найден! Установите Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не найден! Установите Docker Compose"
        exit 1
    fi

    if ! command -v python3 &> /dev/null; then
        log_error "Python3 не найден! Установите Python 3.8+"
        exit 1
    fi

    log_success "Все зависимости найдены"
}

# Создание необходимых директорий и файлов
setup_project() {
    log_info "Настройка проекта..."

    # Создание директорий
    mkdir -p {models,logs}

    # Создание .env файла
    if [[ ! -f .env ]]; then
        log_info "Создание .env файла..."
        cat > .env << EOF
REDIS_HOST=redis
REDIS_PORT=6379
WHISPER_MODEL=large-v2
JOBS_QUEUE=transcription_jobs
RESULTS_QUEUE=transcription_results
WHISPER_THREADS=8
WHISPER_LANGUAGE=auto
LOG_LEVEL=INFO
EOF
        log_success ".env файл создан"
    fi

    # Создание Docker сети
    if ! docker network ls | grep -q dreamscribe-network; then
        log_info "Создание Docker сети..."
        docker network create dreamscribe-network
        log_success "Сеть dreamscribe-network создана"
    fi
}

# Меню действий
show_menu() {
    echo -e "${CYAN}======================================${NC}"
    echo -e "${PURPLE}🚀 Whisper DreamScribe Manager${NC}"
    echo -e "${CYAN}======================================${NC}"
    echo
    echo "1. 📥 Скачать модель"
    echo "2. 🔨 Собрать и запустить"
    echo "3. ▶️  Запустить (без пересборки)"
    echo "4. 🧹 Полная пересборка"
    echo "5. 🛑 Остановить сервисы"
    echo "6. 📋 Показать логи"
    echo "7. 📊 Статус сервисов"
    echo "8. 🧽 Очистить систему"
    echo "9. 🚪 Выход"
    echo
}

# Скачивание модели
download_model() {
    log_info "Скачивание модели..."
    python3 scripts/download-model.py
    if [[ $? -eq 0 ]]; then
        log_success "Модель скачана успешно"
    else
        log_error "Ошибка скачивания модели"
        return 1
    fi
}

# Сборка и запуск
build_and_run() {
    log_info "Сборка образа..."
    docker-compose -f docker/docker-compose.yml build

    if [[ $? -eq 0 ]]; then
        log_success "Образ собран"
        start_services
    else
        log_error "Ошибка сборки образа"
        return 1
    fi
}

# Запуск сервисов
start_services() {
    log_info "Запуск сервисов..."
    docker-compose -f docker/docker-compose.yml up -d

    if [[ $? -eq 0 ]]; then
        log_success "Сервисы запущены!"
        show_useful_commands
    else
        log_error "Ошибка запуска сервисов"
        return 1
    fi
}

# Полная пересборка
full_rebuild() {
    log_info "Полная пересборка системы..."
    docker-compose -f docker/docker-compose.yml down
    docker system prune -f
    docker-compose -f docker/docker-compose.yml build --no-cache
    start_services
}

# Остановка сервисов
stop_services() {
    log_info "Остановка сервисов..."
    docker-compose -f docker/docker-compose.yml down
    log_success "Сервисы остановлены"
}

# Показать логи
show_logs() {
    log_info "Показ логов (Ctrl+C для выхода)..."
    docker-compose -f docker/docker-compose.yml logs -f whisper-dreamscribe
}

# Статус сервисов
show_status() {
    log_info "Статус сервисов:"
    docker-compose -f docker/docker-compose.yml ps
    echo
    log_info "Использование ресурсов:"
    docker stats whisper-dreamscribe --no-stream 2>/dev/null || log_warning "Контейнер не запущен"
}

# Очистка системы
cleanup_system() {
    log_warning "Очистка системы Docker..."
    read -p "Вы уверены? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f docker/docker-compose.yml down
        docker system prune -a -f
        docker volume prune -f
        log_success "Система очищена"
    fi
}

# Полезные команды
show_useful_commands() {
    echo
    log_info "Полезные команды:"
    echo "  docker-compose -f docker/docker-compose.yml ps           - статус контейнеров"
    echo "  docker-compose -f docker/docker-compose.yml logs -f      - логи всех сервисов"
    echo "  docker-compose -f docker/docker-compose.yml stop         - остановка сервисов"
    echo "  docker stats whisper-dreamscribe                        - мониторинг ресурсов"
}

# Основная функция
main() {
    echo -e "${GREEN}🎉 Добро пожаловать в Whisper DreamScribe!${NC}"
    echo -e "${CYAN}Система: $(detect_os)${NC}"
    echo

    check_dependencies
    setup_project

    while true; do
        show_menu
        read -p "Выберите действие (1-9): " choice

        case $choice in
            1) download_model ;;
            2) build_and_run ;;
            3) start_services ;;
            4) full_rebuild ;;
            5) stop_services ;;
            6) show_logs ;;
            7) show_status ;;
            8) cleanup_system ;;
            9)
                log_info "До свидания!"
                exit 0
                ;;
            *)
                log_error "Неверный выбор. Попробуйте снова."
                ;;
        esac

        echo
        read -p "Нажмите Enter для продолжения..."
        echo
    done
}

# Запуск
main "$@"
