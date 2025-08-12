#!/usr/bin/env python3
"""
Современный скрипт для скачивания моделей Whisper в папку проекта.
Совместим с новой архитектурой на основе Pydantic Settings.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any

# Добавляем корневую папку в PYTHONPATH для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.config import settings
    USE_PROJECT_CONFIG = True
except ImportError:
    # Fallback если запускается вне проекта
    USE_PROJECT_CONFIG = False

# Доступные модели
MODELS: Dict[str, Dict[str, Any]] = {
    'tiny': {
        'size': '39MB',
        'quality': 'Базовое',
        'speed': 'Очень быстро',
        'accuracy': '~70%'
    },
    'base': {
        'size': '142MB',
        'quality': 'Удовлетворительное',
        'speed': 'Быстро',
        'accuracy': '~80%'
    },
    'small': {
        'size': '466MB',
        'quality': 'Хорошее',
        'speed': 'Средне',
        'accuracy': '~85%'
    },
    'medium': {
        'size': '1.5GB',
        'quality': 'Очень хорошее',
        'speed': 'Медленно',
        'accuracy': '~90%'
    },
    'large-v2': {
        'size': '2.9GB',
        'quality': 'Максимальное',
        'speed': 'Очень медленно',
        'accuracy': '~95%'
    }
}

def print_colored(text: str, color: str = "") -> None:
    """Печать цветного текста с поддержкой Windows."""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
        'end': '\033[0m'
    }

    if platform.system() == 'Windows':
        try:
            # Включаем ANSI поддержку на Windows 10+
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            # Если не получилось - печатаем без цветов
            print(text)
            return

    color_code = colors.get(color, '')
    end_code = colors.get('end', '')
    print(f"{color_code}{text}{end_code}")

def load_env_model() -> str:
    """Загружает название модели из конфигурации."""
    if USE_PROJECT_CONFIG:
        return settings.whisper_model

    # Fallback - чтение из .env файла
    env_file = Path('.env')
    if not env_file.exists():
        return 'large-v2'

    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('WHISPER_MODEL='):
                    return line.split('=', 1)[1].strip()
    except Exception:
        pass

    return 'large-v2'

def check_system_requirements() -> bool:
    """Проверяет системные требования."""
    print_colored("🔍 Проверка системных требований...", "blue")

    # Проверка Python
    if sys.version_info < (3, 8):
        print_colored(f"❌ Требуется Python 3.8+. Текущая версия: {sys.version}", "red")
        return False
    print_colored(f"✅ Python {sys.version.split()[0]} найден", "green")

    # Проверка pip
    try:
        subprocess.run([sys.executable, '-m', 'pip', '--version'],
                      check=True, capture_output=True)
        print_colored("✅ pip найден", "green")
    except subprocess.CalledProcessError:
        print_colored("❌ pip не найден", "red")
        return False

    return True

def install_faster_whisper() -> bool:
    """Устанавливает faster-whisper если не установлен."""
    try:
        import faster_whisper
        print_colored("✅ faster-whisper уже установлен", "green")
        return True
    except ImportError:
        print_colored("📦 Установка faster-whisper...", "yellow")
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install',
                'faster-whisper>=1.0.0', '--upgrade'
            ], check=True, capture_output=True)
            print_colored("✅ faster-whisper установлен", "green")
            return True
        except subprocess.CalledProcessError as e:
            print_colored(f"❌ Ошибка установки faster-whisper: {e}", "red")
            return False

def check_disk_space(model_name: str, models_dir: Path) -> bool:
    """Проверяет доступное место на диске."""
    model_sizes = {
        'tiny': 50,      # MB
        'base': 200,     # MB
        'small': 500,    # MB
        'medium': 1600,  # MB
        'large-v2': 3000 # MB
    }

    required_mb = model_sizes.get(model_name, 1000)

    try:
        free_bytes = os.statvfs(models_dir).f_frsize * os.statvfs(models_dir).f_bavail
        free_mb = free_bytes / (1024 * 1024)
    except AttributeError:
        # Windows
        import shutil
        free_bytes = shutil.disk_usage(models_dir).free
        free_mb = free_bytes / (1024 * 1024)

    if free_mb < required_mb:
        print_colored(f"❌ Недостаточно места на диске. Требуется: {required_mb}MB, доступно: {free_mb:.0f}MB", "red")
        return False

    print_colored(f"✅ Достаточно места на диске: {free_mb:.0f}MB доступно", "green")
    return True

def download_model(model_name: str, models_dir: Path) -> bool:
    """Скачивает модель в папку проекта."""
    # Проверяем возможные пути к модели
    possible_paths = [
        models_dir / model_name,
        models_dir / f"models--Systran--faster-whisper-{model_name}",
    ]

    # Проверяем, не скачана ли уже модель
    for model_path in possible_paths:
        if model_path.exists() and any(model_path.iterdir()):
            print_colored(f"✅ Модель {model_name} уже существует в {model_path}", "green")
            return True

    if not check_disk_space(model_name, models_dir):
        return False

    try:
        model_info = MODELS[model_name]
        print_colored(f"📥 Скачивание модели {model_name}:", "blue")
        print_colored(f"   📊 Размер: {model_info['size']}", "cyan")
        print_colored(f"   🎯 Качество: {model_info['quality']} ({model_info['accuracy']})", "cyan")
        print_colored(f"   ⚡ Скорость: {model_info['speed']}", "cyan")
        print_colored(f"   📁 Путь: {models_dir}", "cyan")

        # Создаем директорию для моделей
        models_dir.mkdir(parents=True, exist_ok=True)

        # Устанавливаем переменные окружения для кэша
        os.environ['HF_HOME'] = str(models_dir)
        os.environ['TRANSFORMERS_CACHE'] = str(models_dir)

        # Импортируем и создаем модель
        from faster_whisper import WhisperModel

        print_colored("⏳ Инициализация загрузки...", "yellow")

        model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
            download_root=str(models_dir)
        )

        print_colored(f"✅ Модель {model_name} успешно скачана!", "green")
        print_colored(f"📁 Расположение: {models_dir}", "green")

        # Показываем информацию о скачанных файлах
        downloaded_path = None
        for path in possible_paths:
            if path.exists():
                downloaded_path = path
                break

        if downloaded_path:
            files = list(downloaded_path.rglob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            total_size_mb = total_size / (1024 * 1024)
            print_colored(f"📦 Скачано файлов: {len(files)}, общий размер: {total_size_mb:.1f}MB", "cyan")

        return True

    except Exception as e:
        print_colored(f"❌ Ошибка при скачивании {model_name}: {e}", "red")

        # Удаляем частично скачанные папки
        for path in possible_paths:
            if path.exists():
                import shutil
                try:
                    shutil.rmtree(path, ignore_errors=True)
                    print_colored(f"🧹 Удалена частично скачанная папка: {path}", "yellow")
                except:
                    pass

        return False

def list_models() -> None:
    """Показывает список доступных моделей в красивом формате."""
    print_colored("📋 Доступные модели Whisper:", "bold")
    print()

    # Заголовок таблицы
    header = f"{'Модель':<12} {'Размер':<8} {'Точность':<10} {'Качество':<18} {'Скорость':<15}"
    print_colored(header, "cyan")
    print_colored("-" * len(header), "cyan")

    # Строки таблицы
    for name, info in MODELS.items():
        line = f"{name:<12} {info['size']:<8} {info['accuracy']:<10} {info['quality']:<18} {info['speed']:<15}"
        print_colored(line, "white")

    print()
    print_colored("💡 Рекомендации:", "yellow")
    print_colored("   • tiny/base - для быстрого тестирования", "white")
    print_colored("   • small/medium - для production с ограниченными ресурсами", "white")
    print_colored("   • large-v2 - для максимального качества", "white")

def interactive_mode() -> str:
    """Интерактивный режим выбора модели."""
    print_colored("🤖 Интерактивный выбор модели", "bold")
    print()

    models_list = list(MODELS.keys())
    for i, (name, info) in enumerate(MODELS.items(), 1):
        print_colored(f"{i}. {name:<12} - {info['size']:<8} - {info['quality']} ({info['accuracy']})", "white")

    print()

    while True:
        try:
            choice = input("Введите номер модели (1-5): ").strip()
            choice_num = int(choice)

            if 1 <= choice_num <= len(MODELS):
                selected_model = models_list[choice_num - 1]
                print_colored(f"✅ Выбрана модель: {selected_model}", "green")
                return selected_model
            else:
                print_colored("❌ Неверный номер. Попробуйте снова.", "red")

        except ValueError:
            print_colored("❌ Введите число от 1 до 5.", "red")
        except KeyboardInterrupt:
            print_colored("\n👋 Выход из программы", "yellow")
            sys.exit(0)

def main() -> None:
    """Главная функция."""
    print_colored("=" * 60, "cyan")
    print_colored("🚀 Загрузчик моделей Whisper DreamScribe", "bold")
    print_colored(f"💻 Система: {platform.system()} {platform.release()}", "cyan")
    print_colored("=" * 60, "cyan")
    print()

    # Проверки системы
    if not check_system_requirements():
        sys.exit(1)

    if not install_faster_whisper():
        sys.exit(1)

    # Определяем модель для скачивания
    model_name = None

    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['--list', '-l', 'list']:
            list_models()
            return
        elif arg in ['--interactive', '-i', 'interactive']:
            model_name = interactive_mode()
        elif arg in MODELS:
            model_name = arg
        else:
            print_colored(f"❌ Неизвестная модель или команда: {arg}", "red")
            list_models()
            sys.exit(1)

    # Из конфигурации проекта или .env файла
    if not model_name:
        model_name = load_env_model()
        if model_name != 'large-v2':  # Если не дефолтное значение
            print_colored(f"📋 Модель из конфигурации: {model_name}", "blue")
        else:
            # Интерактивный режим если не указана модель
            print_colored("🤖 Модель не указана, переход в интерактивный режим", "yellow")
            model_name = interactive_mode()

    # Проверяем корректность модели
    if model_name not in MODELS:
        print_colored(f"❌ Неизвестная модель: {model_name}", "red")
        list_models()
        sys.exit(1)

    # Создаем папку для моделей
    models_dir = Path('./models')
    models_dir.mkdir(exist_ok=True)

    print()
    print_colored(f"🎯 Скачивание модели: {model_name}", "blue")

    # Скачиваем модель
    if download_model(model_name, models_dir):
        print()
        print_colored("🎉 Модель готова к использованию!", "green")
        print_colored("🐳 Теперь можете запускать Docker контейнер", "blue")
        print_colored("📋 Команды:", "cyan")
        print_colored("   scripts\\deploy.bat    - Windows", "white")
        print_colored("   ./scripts/deploy.sh   - Linux/macOS", "white")
    else:
        print_colored("❌ Не удалось скачать модель", "red")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n👋 Скачивание прервано пользователем", "yellow")
        sys.exit(0)
    except Exception as e:
        print_colored(f"\n❌ Неожиданная ошибка: {e}", "red")
        import traceback
        traceback.print_exc()
        sys.exit(1)
