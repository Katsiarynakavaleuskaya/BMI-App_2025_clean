# 🔐 РУКОВОДСТВО ПО НАСТРОЙКЕ СЕКРЕТОВ

## 📍 ОСНОВНЫЕ МЕСТА ДЛЯ ДОБАВЛЕНИЯ СЕКРЕТОВ:

### 1. **ФАЙЛ `.env` (ГЛАВНОЕ МЕСТО)**
```bash
# Расположение: /home/runner/work/BMI-App_2025_clean/BMI-App_2025_clean/.env
```

**Обязательные секреты:**
```env
# API ключ для премиум функций
API_KEY=your_secret_api_key_here

# API ключ для X.AI/Grok
XAI_API_KEY=your_xai_api_key_here
```

### 2. **ФАЙЛЫ ДЛЯ ТЕСТИРОВАНИЯ**
```bash
# Для тестов:
tests/tmp_secret.txt       - API_KEY="1234567890abcdefABCDEF"
tests/_tmp_secret.txt      - API_KEY="aaaaaaaaaaaaaaaaaaaa"
```

### 3. **ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ (ПРОДАКШЕН)**
```bash
export API_KEY="your_production_key"
export XAI_API_KEY="your_xai_production_key"
```

## 🔧 НАСТРОЙКА:

### Шаг 1: Создать .env файл
```bash
cp .env.example .env
```

### Шаг 2: Заполнить секреты
Откройте `.env` и замените:
- `your_api_key_here` → ваш настоящий API ключ
- `your_xai_api_key_here` → ваш X.AI API ключ

### Шаг 3: Проверить настройки
```bash
# Запустить приложение
uvicorn app:app --reload

# Проверить эндпоинт с API ключом
curl -H "X-API-Key: your_api_key_here" http://localhost:8000/api/v1/bmi
```

## 🛡️ БЕЗОПАСНОСТЬ:

⚠️ **ВАЖНО:**
- Никогда не коммитьте `.env` файл в git
- Используйте `.env.example` как шаблон
- В продакшене используйте переменные окружения

## 📝 ИСПОЛЬЗОВАНИЕ В КОДЕ:

Секреты проверяются в `app.py`:
```python
# Строка 171: Получение API ключа из окружения
expected = os.getenv("API_KEY")

# Строка 167: Заголовок для API ключа
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
```

## 🧪 ТЕСТИРОВАНИЕ:

```bash
# Запуск с тестовым API ключом
API_KEY=test_key python -m pytest tests/

# Запуск с секретами из .env
python -m uvicorn app:app --reload
```