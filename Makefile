.PHONY: help install dev-install build run stop logs status clean test lint format docker-build docker-push

# Переменные
IMAGE_NAME = whisper-dreamscribe
TAG = latest
REGISTRY = your-username

# Помощь
help:
	@echo "🚀 Whisper DreamScribe - Команды для разработки"
	@echo ""
	@echo "📦 Установка:"
	@echo "  install      - Установить зависимости"
	@echo "  dev-install  - Установить dev зависимости"
	@echo ""
	@echo "🔨 Разработка:"
	@echo "  format       - Форматировать код (black, isort)"
	@echo "  lint         - Проверить код (mypy, flake8)"
	@echo "  test         - Запустить тесты"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  build        - Собрать Docker образ"
	@echo "  run          - Запустить сервисы"
	@echo "  stop         - Остановить сервисы"
	@echo "  logs         - Показать логи"
	@echo "  status       - Статус сервисов"
	@echo "  clean        - Очистить систему"
	@echo ""
	@echo "📤 Публикация:"
	@echo "  docker-push  - Опубликовать образ"

# Установка
install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

# Форматирование и линтинг
format:
	black src/ scripts/
	isort src/ scripts/

lint:
	mypy src/
	flake8 src/

test:
	pytest tests/

# Docker команды
build:
	docker-compose -f docker/docker-compose.yml build

run:
	docker-compose -f docker/docker-compose.yml up -d

stop:
	docker-compose -f docker/docker-compose.yml down

logs:
	docker-compose -f docker/docker-compose.yml logs -f whisper-dreamscribe

status:
	docker-compose -f docker/docker-compose.yml ps

clean:
	docker-compose -f docker/docker-compose.yml down
	docker system prune -f

# Публикация
docker-build:
	docker build -f docker/Dockerfile -t $(REGISTRY)/$(IMAGE_NAME):$(TAG) .

docker-push: docker-build
	docker push $(REGISTRY)/$(IMAGE_NAME):$(TAG)
