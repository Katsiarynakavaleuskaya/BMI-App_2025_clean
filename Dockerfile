FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# HF Spaces пробрасывает порт через переменную окружения $PORT
ENV PORT=7860
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT}
