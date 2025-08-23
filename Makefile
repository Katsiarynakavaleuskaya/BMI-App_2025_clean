.PHONY: run test cov kill health

run:
	uvicorn app:app --reload --port 8001

test:
	pytest -q

cov:
	pytest --cov=bmi_core --cov-report=term-missing

kill:
	-pkill -f "uvicorn app:app --reload --port 8001" || true
	-lsof -ti :8001 | xargs -r kill -9 || true

health:
	curl -s http://127.0.0.1:8001/health && echo
