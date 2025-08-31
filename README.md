# BMI-App 2025 (FastAPI)
[![python-tests](https://github.com/Katsiarynakavaleuskaya/BMI-App_2025_clean/actions/workflows/python-tests.yml/badge.svg)](https://github.com/Katsiarynakavaleuskaya/BMI-App_2025_clean/actions/workflows/python-tests.yml)

Приложение для расчёта BMI на FastAPI с автотестами, покрытием и Docker.

---

## 🚀 Quick Start

### 1) Локальный запуск (venv)

```bash
make venv
source .venv/bin/activate
make dev
# откроется на http://127.0.0.1:8001/docs
```

### 2) Docker

```bash
make docker-build
make docker-run
```

---

## 📋 API Endpoints

### Health & Monitoring

- `GET /health` - Health check
- `GET /api/v1/health` - V1 health check
- `GET /metrics` - Uptime metrics
- `GET /privacy` - Privacy policy

### BMI Calculation

- `POST /bmi` - Legacy BMI endpoint
- `POST /api/v1/bmi` - V1 BMI calculation (requires X-API-Key header)
  - Input: `{"weight_kg": 70, "height_cm": 170, "group": "general"}`
  - Output: `{"bmi": 24.22, "category": "Healthy weight", "interpretation": ""}`

### Web UI

- `GET /` - Simple web interface for BMI calculation

### Body Fat Estimation

- `POST /api/v1/bodyfat` - Body fat percentage estimation

### Insight (AI-powered)

- `POST /api/v1/insight` - AI insight on text (requires X-API-Key header)
  - Input: `{"text": "I feel tired"}`
  - Output: `{"provider": "stub", "insight": "insight::deriat"}`

---

## 🔧 Development

### Testing

```bash
make test
make coverage
```

### Linting

```bash
make lint
```

---

## 🔒 Security & Compliance

- API Key authentication for sensitive endpoints
- Optional rate limiting with SlowAPI
- GDPR compliance for health data (no storage, privacy policy)
- Property-based testing with Hypothesis for robustness

---

## 📊 Features

- **Asynchronous Endpoints**: All endpoints are now async for better concurrency and scalability
- BMI calculation with categories
- Body fat estimation using multiple formulas
- AI insights via configurable LLM providers (Stub, Grok, Ollama) with retry mechanisms
- Comprehensive test suite with 100% coverage goal
- Docker support
- CI/CD with GitHub Actions
- Simple web UI at root path for easy BMI calculation
- Structured logging and request monitoring
- Security hardening with automated dependency updates and scans

