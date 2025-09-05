#!/usr/bin/env python3
"""
Демонстрация работы с секретами в BMI-App_2025_clean
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_env_loading():
    """Тестирует загрузку переменных окружения из .env"""
    print("🔍 ПРОВЕРКА ЗАГРУЗКИ СЕКРЕТОВ:")
    print("=" * 50)
    
    # Проверяем существование .env файла
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"✅ .env файл найден: {env_file}")
    else:
        print(f"❌ .env файл не найден: {env_file}")
        return False
    
    # Загружаем .env
    try:
        import dotenv
        dotenv.load_dotenv(env_file)
        print("✅ .env файл успешно загружен")
    except ImportError:
        print("❌ python-dotenv не установлен")
        return False
    except Exception as e:
        print(f"❌ Ошибка загрузки .env: {e}")
        return False
    
    # Проверяем ключевые переменные
    api_key = os.getenv("API_KEY")
    xai_key = os.getenv("XAI_API_KEY")
    
    print(f"📋 API_KEY: {'✅ Установлен' if api_key else '❌ Не установлен'}")
    print(f"📋 XAI_API_KEY: {'✅ Установлен' if xai_key else '❌ Не установлен'}")
    
    if api_key and api_key != "your_api_key_here":
        print(f"📋 API_KEY (первые 8 символов): {api_key[:8]}...")
    elif api_key == "your_api_key_here":
        print("⚠️  API_KEY содержит значение по умолчанию - замените на настоящий ключ")
    
    return True

def test_api_key_validation():
    """Тестирует валидацию API ключей"""
    print("\n🔐 ПРОВЕРКА ВАЛИДАЦИИ API КЛЮЧЕЙ:")
    print("=" * 50)
    
    try:
        from app import get_api_key, api_key_header
        print("✅ Функции валидации API ключей импортированы")
        print(f"✅ Заголовок API ключа: {api_key_header.model.name}")
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    
    # Тест с правильным ключом
    try:
        api_key = os.getenv("API_KEY")
        if api_key:
            # Эмулируем вызов с правильным ключом
            os.environ["API_KEY"] = api_key
            result = get_api_key(api_key)
            print(f"✅ Валидация с правильным ключом: {'Успешно' if result == api_key else 'Ошибка'}")
        else:
            print("⚠️  API_KEY не установлен, пропускаем тест валидации")
    except Exception as e:
        print(f"❌ Ошибка валидации: {e}")
    
    return True

def show_protected_endpoints():
    """Показывает защищенные эндпоинты"""
    print("\n🛡️  ЗАЩИЩЕННЫЕ ЭНДПОИНТЫ:")
    print("=" * 50)
    
    protected_endpoints = [
        "/api/v1/bmi",
        "/api/v1/premium/bmr", 
        "/api/v1/premium/plate",
        "/api/v1/premium/targets",
        "/api/v1/premium/gaps",
        "/api/v1/admin/db-status",
        "/api/v1/admin/force-update",
        "/api/v1/bmi/pro",
        "/api/v1/insight"
    ]
    
    for endpoint in protected_endpoints:
        print(f"🔒 {endpoint}")
    
    print(f"\n📋 Всего защищенных эндпоинтов: {len(protected_endpoints)}")
    print("💡 Для доступа используйте заголовок: X-API-Key: ваш_ключ")

def main():
    """Главная функция демонстрации"""
    print("🚀 ДЕМОНСТРАЦИЯ РАБОТЫ С СЕКРЕТАМИ")
    print("=" * 50)
    print(f"📁 Проект: {project_root.name}")
    print(f"📂 Путь: {project_root}")
    
    # Запускаем тесты
    test_env_loading()
    test_api_key_validation()
    show_protected_endpoints()
    
    print("\n✨ РЕЗЮМЕ:")
    print("=" * 50)
    print("1. Создайте .env файл на основе .env.example")
    print("2. Замените 'your_api_key_here' на настоящий API ключ")
    print("3. Замените 'your_xai_api_key_here' на настоящий X.AI ключ")
    print("4. Запустите приложение: uvicorn app:app --reload")
    print("5. Используйте заголовок X-API-Key для доступа к защищенным эндпоинтам")

if __name__ == "__main__":
    main()