#!/usr/bin/env python3
"""
Скрипт для скачивания конкретной модели Whisper в папку проекта
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

# Доступные модели
MODELS = {
    'tiny': {'size': '39MB', 'quality': 'Базовое'},
    'base': {'size': '142MB', 'quality': 'Удовлетворительное'},
    'small': {'size': '466MB', 'quality': 'Хорошее'},
    'medium': {'size': '1.5GB', 'quality': 'Очень хорошее'},
    'large-v2': {'size': '2.9GB', 'quality': 'Максимальное'}
}

def load_env_model():
    """Загружает название модели из .env файла"""
    env_file = Path('.env')
    if not env_file.exists():
        return None

    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('WHISPER_MODEL='):
                    return line.split('=', 1)[1].strip()
    except Exception:
        pass

    return None

def check_python():
    """Проверяет версию Python"""
    if sys.version_info < (3, 8):
        print(f"❌ Требуется Python 3.8+. Текущая версия: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} найден")
    return True

def install_faster_whisper():
    """Устанавливает faster-whisper если не установлен"""
    try:
        import faster_whisper
        print("✅ faster-whisper уже установлен")
        return True
    except ImportError:
        print("📦 Установка faster-whisper...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'faster-whisper>=1.0.0'],
                           check=True, capture_output=True)
            print("✅ faster-whisper установлен")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки faster-whisper: {e}")
            return False

def download_model(model_name: str, models_dir: Path):
    """Скачивает модель в папку проекта"""
    model_path = models_dir / model_name

    # Проверяем, не скачана ли уже модель
    if model_path.exists() and any(model_path.iterdir()):
        print(f"✅ Модель {model_name} уже существует в {model_path}")
        return True

    try:
        print(f"📥 Скачивание модели {model_name} ({MODELS[model_name]['size']})...")
        print(f"📁 Путь сохранения: {model_path}")

        # Создаем директорию для модели
        model_path.mkdir(parents=True, exist_ok=True)

        # Устанавливаем переменные окружения для кэша
        os.environ['HF_HOME'] = str(models_dir)
        os.environ['TRANSFORMERS_CACHE'] = str(models_dir)

        # Импортируем и создаем модель
        from faster_whisper import WhisperModel

        model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
            download_root=str(models_dir)
        )

        print(f"✅ Модель {model_name} успешно скачана!")
        print(f"📊 Качество: {MODELS[model_name]['quality']}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при скачивании {model_name}: {e}")
        # Удаляем частично скачанную папку
        if model_path.exists():
            import shutil
            shutil.rmtree(model_path, ignore_errors=True)
        return False

def main():
    print("=" * 50)
    print("🚀 Загрузчик модели Whisper для проекта")
    print("=" * 50)

    # Проверки
    if not check_python():
        sys.exit(1)

    if not install_faster_whisper():
        sys.exit(1)

    # Определяем модель для скачивания
    model_name = None

    # Из аргументов командной строки
    if len(sys.argv) > 1:
        model_name = sys.argv[1]

    # Из .env файла
    if not model_name:
        model_name = load_env_model()
        if model_name:
            print(f"📋 Модель из .env файла: {model_name}")

    # По умолчанию
    if not model_name:
        model_name = 'large-v2'
        print(f"📋 Используется модель по умолчанию: {model_name}")

    # Проверяем корректность модели
    if model_name not in MODELS:
        print(f"❌ Неизвестная модель: {model_name}")
        print("📋 Доступные модели:")
        for name, info in MODELS.items():
            print(f"   {name:<12} - {info['size']:<8} - {info['quality']}")
        sys.exit(1)

    # Создаем папку для моделей
    models_dir = Path('./models')
    models_dir.mkdir(exist_ok=True)

    # Скачиваем модель
    print()
    if download_model(model_name, models_dir):
        print()
        print("🎉 Модель готова к использованию!")
        print(f"📁 Расположение: {models_dir / model_name}")
        print("🐳 Теперь можете запускать Docker контейнер")
    else:
        print("❌ Не удалось скачать модель")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Скачивание прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)
