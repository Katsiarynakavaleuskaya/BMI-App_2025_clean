# BMI-App Core (RU/EN)

Чистая доменная логика BMI + WHtR с тестами.

- RU/EN локализация
- Группы: general, athlete (спорт-мод), pregnant, elderly, child
- Здоровый диапазон ИМТ (для 60+ верх 27.5; для athlete+premium верх ≥ 27.0)
- План действий: maintain / lose / gain (+ советы)
- Тесты: pytest (покрытие ~98%)

## Установка
```bash
conda create -n bmi-app-2025 python=3.11 -y
conda activate bmi-app-2025
pip install -r requirements.txt
