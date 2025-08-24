# BMI-App 2025 (FastAPI)

![tests](https://github.com/Katsiarynakavaleuskaya/BMI-App_2025_clean/actions/workflows/python-tests.yml/badge.svg)

## RU

### Быстрый старт
```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8001
# http://127.0.0.1:8001/health


### Эндпоинты
- `GET /health` – проверка статуса
- `POST /bmi` – расчёт BMI (RU/EN)
- `POST /plan` – персональный план
- `POST /insight` – экспериментальная LLM-фича (включается флагом)

### Фиче-флаги
```bash
export FEATURE_INSIGHT=1
export LLM_PROVIDER=stub

md

### Примеры curl
```bash
# BMI (EN)
curl -s -X POST http://127.0.0.1:8001/bmi -H "Content-Type: application/json" \
  -d '{"weight_kg":70,"height_m":1.75,"age":30,"gender":"male","pregnant":"no","athlete":"no","waist_cm":80,"lang":"en"}'

# План (RU, premium)
curl -s -X POST http://127.0.0.1:8001/plan -H "Content-Type: application/json" \
  -d '{"weight_kg":85,"height_m":1.80,"age":28,"gender":"муж","pregnant":"нет","athlete":"спортсмен","waist_cm":82,"lang":"ru","premium":true}'

