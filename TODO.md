# 📋 TODO - BMI App 2025

## 🚀 Текущий спринт: ES-локализация и покрытие ≥96%

### 📅 Статус: Готов к выполнению завтра

**⚠️ ВАЖНО: Каждая задача выполняется по схеме:**
1. ✅ Выполнить задачу
2. 🧪 Запустить тесты
3. 📊 Проверить покрытие
4. 🚀 Пуш в git
5. ➡️ Только потом следующая задача

---

### 📝 Задачи спринта

- [ ] **1. Добавить _life_stage_warnings() и локализованные тексты (RU/EN/ES)**
  - Файл: `core/targets.py`
  - Тест: `pytest tests/test_premium_targets_lifestage.py -q`

- [ ] **2. Включить предупреждения в ответ /premium/targets**
  - Файл: `app/routers/premium_targets.py`
  - Тест: `pytest tests/test_premium_targets_lifestage.py -q`

- [ ] **3. Добавить/проверить Pydantic-валидации → 422-тесты**
  - Файл: `tests/test_premium_targets_422.py`
  - Тест: `pytest tests/test_premium_targets_422.py -q`

- [ ] **4. Реализовать/агрегировать day_micros в /premium/plate**
  - Файл: `app/routers/premium_plate.py`
  - Тест: `pytest tests/test_premium_plate.py -q`

- [ ] **5. Написать интеграционный тест покрытия Plate→Targets**
  - Файл: `tests/test_plate_coverage_integration.py`
  - Тест: `pytest tests/test_plate_coverage_integration.py -q`

- [ ] **6. Создать test_premium_targets_i18n_es.py (snapshot)**
  - Файл: `tests/test_premium_targets_i18n_es.py`
  - Тест: `pytest tests/test_premium_targets_i18n_es.py -q`

- [ ] **7. Обновить Docs: Sources & Units + ES curl-пример**
  - Файл: `docs/PREMIUM_TARGETS_API.md` или `README.md`
  - Тест: Проверить документацию

- [ ] **8. Прогнать pytest -q и проверить покрытие ≥96%**
  - Команда: `pytest --cov=. --cov-report=term-missing`
  - Цель: Покрытие ≥96%

- [ ] **9. Запушить изменения в git**
  - Команда: `git add . && git commit -m "..." && git push`

---

## 📊 Текущие метрики

- **Покрытие кода**: 94.34% (цель: ≥96%)
- **Тесты**: 1137 passed, 10 skipped, 1 xfailed
- **CI/CD**: Настроен на 94% (требуется обновление до 96%)
- **Статус**: Все тесты проходят ✅

---

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

---

## 📚 Ресурсы

- **План спринта**: `SPRINT_PLAN_ES_LOCALIZATION.md`
- **Готовые шаблоны**: `CODE_TEMPLATES_ES_LOCALIZATION.md`
- **CI/CD конфигурация**: `.github/workflows/ci.yml`
- **Настройки покрытия**: `.coveragerc`

---

## 🎯 Цели спринта

- ✅ ES локализация работает
- ✅ Life stage warnings реализованы
- ✅ 422 тесты добавлены
- ✅ Plate→Targets интеграция
- ✅ Покрытие ≥96%
- ✅ Документация обновлена
- ✅ CI/CD проходит

---

## 📝 Заметки

- Все готовые шаблоны кода уже созданы в `CODE_TEMPLATES_ES_LOCALIZATION.md`
- План выполнения детально описан в `SPRINT_PLAN_ES_LOCALIZATION.md`
- Текущее покрытие 94.34% - нужно добавить ~2% для достижения цели
- Все тесты проходят, CI/CD настроен корректно

---

**🚀 Готов к выполнению! Начинаем с первой задачи завтра.**
