# 📋 План спринта: ES-локализация и покрытие ≥96%

## 🎯 Цель спринта
Зафиксировать локализацию ES тестами и доками, закрыть предупреждения по life_stage, добавить негативные кейсы (422), сделать мини-интеграцию Plate→Targets, добить покрытие ≥96%.

## 📝 Пошаговый план выполнения

**⚠️ ВАЖНО: Каждая задача выполняется по схеме:**
1. ✅ Выполнить задачу
2. 🧪 Запустить тесты
3. 📊 Проверить покрытие
4. 🚀 Пуш в git
5. ➡️ Только потом следующая задача

---

### 1️⃣ **Добавить _life_stage_warnings() и локализованные тексты (RU/EN/ES)**
- **Файл**: `core/targets.py` (или соответствующий слой)
- **Задача**: Реализовать функцию с локализованными сообщениями для teen/pregnant/51+
- **Тест**: `pytest tests/test_premium_targets_lifestage.py -q`

### 2️⃣ **Включить предупреждения в ответ /premium/targets**
- **Файл**: `app/routers/premium_targets.py`
- **Задача**: Интегрировать warnings в API ответ
- **Тест**: `pytest tests/test_premium_targets_lifestage.py -q`

### 3️⃣ **Добавить/проверить Pydantic-валидации → 422-тесты**
- **Файл**: `tests/test_premium_targets_422.py`
- **Задача**: Создать тесты для невалидных sex/activity/goal/lang
- **Тест**: `pytest tests/test_premium_targets_422.py -q`

### 4️⃣ **Реализовать/агрегировать day_micros в /premium/plate**
- **Файл**: `app/routers/premium_plate.py`
- **Задача**: Добавить агрегацию микроэлементов по дню
- **Тест**: `pytest tests/test_premium_plate.py -q`

### 5️⃣ **Написать интеграционный тест покрытия Plate→Targets**
- **Файл**: `tests/test_plate_coverage_integration.py`
- **Задача**: Тест покрытия Fe/Ca/Mg/K между Plate и Targets
- **Тест**: `pytest tests/test_plate_coverage_integration.py -q`

### 6️⃣ **Создать test_premium_targets_i18n_es.py (snapshot)**
- **Файл**: `tests/test_premium_targets_i18n_es.py`
- **Задача**: Snapshot-тест для ES локализации
- **Тест**: `pytest tests/test_premium_targets_i18n_es.py -q`

### 7️⃣ **Обновить Docs: Sources & Units + ES curl-пример**
- **Файл**: `docs/PREMIUM_TARGETS_API.md` или `README.md`
- **Задача**: Добавить секцию Sources & Units с ES примером
- **Тест**: Проверить документацию

### 8️⃣ **Прогнать pytest -q и проверить покрытие ≥96%**
- **Команда**: `pytest --cov=. --cov-report=term-missing`
- **Цель**: Покрытие ≥96%
- **Тест**: Все тесты должны проходить

### 9️⃣ **Запушить изменения в git**
- **Команда**: `git add . && git commit -m "..." && git push`
- **Цель**: Успешный push с прохождением CI/CD

---

## 📊 Критерии успеха
- ✅ Все тесты проходят
- ✅ Покрытие ≥96%
- ✅ CI/CD pipeline проходит
- ✅ ES локализация работает
- ✅ Документация обновлена

## 🔄 Workflow для каждой задачи
```bash
# 1. Выполнить задачу
# 2. Запустить тесты
pytest -q

# 3. Проверить покрытие
pytest --cov=. --cov-report=term-missing

# 4. Пуш в git
git add .
git commit -m "Task description"
git push

# 5. Перейти к следующей задаче
```

## 📅 Статус выполнения
- [ ] 1. Добавить _life_stage_warnings() и локализованные тексты (RU/EN/ES)
- [ ] 2. Включить предупреждения в ответ /premium/targets
- [ ] 3. Добавить/проверить Pydantic-валидации → 422-тесты
- [ ] 4. Реализовать/агрегировать day_micros в /premium/plate
- [ ] 5. Написать интеграционный тест покрытия Plate→Targets
- [ ] 6. Создать test_premium_targets_i18n_es.py (snapshot)
- [ ] 7. Обновить Docs: Sources & Units + ES curl-пример
- [ ] 8. Прогнать pytest -q и проверить покрытие ≥96%
- [ ] 9. Запушить изменения в git

## 📝 Контекст
- Текущее покрытие: 94.34%
- Целевое покрытие: ≥96%
- Требование CI/CD: 94% (уже настроено)
- Все тесты проходят: 1137 passed, 10 skipped, 1 xfailed

## 🚀 Готов к выполнению!
Начинаем с первой задачи завтра.
