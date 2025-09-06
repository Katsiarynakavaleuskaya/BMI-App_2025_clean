SHELL := /bin/bash
PIP ?= . .venv/bin/activate && pip

## Show this help
help:
	@echo "Available targets:" && \
	awk 'BEGIN{FS=":.*##"} /^[a-zA-Z0-9_.-]+:.*##/{printf "  %-22s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## Setup pre-commit hook
pre-commit-setup: ## Install pre-commit hook
	scripts/pre_commit_setup.sh

## Create & install venv deps
venv: ## Create venv and install requirements
	$(PIP) install -U pip
	@if [ -f requirements-dev.txt ]; then $(PIP) install -r requirements-dev.txt; fi
	@if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi

## Run local dev server on :8001
dev: ## Run uvicorn on 0.0.0.0:8001 (reload)
	uvicorn app:app --reload --host 0.0.0.0 --port 8001

## Run tests (quiet)
test: ## Run pytest
	. .venv/bin/activate && pytest -q

## Coverage in terminal + XML (uses .coveragerc)
cov: ## Run coverage with pytest (term + XML)
	. .venv/bin/activate && coverage erase && coverage run -m pytest -q && coverage report -m && coverage xml

## Coverage HTML and open report (uses .coveragerc)
cov-html: ## Generate HTML coverage and open in browser
	. .venv/bin/activate && coverage erase && coverage run -m pytest && coverage html && open htmlcov/index.html

## Lint (ruff)
lint: ## Lint with ruff
	ruff check .

## Auto-fix (ruff)
fmt: ## Format with ruff --fix
	ruff check . --fix || true

## Auto-fix line lengths
fmt-lines: ## Automatically fix line length issues with Ruff
	ruff check . --fix --select=E501

## Show what would be fixed for line lengths
fmt-lines-dry: ## Show what line length issues Ruff would fix
	ruff check . --select=E501

## Check line lengths (PEP 8 compliance)
line-check: ## Check for lines exceeding 79 characters
	scripts/check_line_lengths.sh

## Check line lengths (dry run)
line-check-dry: ## Show files with lines exceeding 79 characters (no changes)
	scripts/check_line_lengths.sh --dry-run

## Add unknown words to dictionary (dry run)
dict-dry-run: ## Show words that would be added to dictionary
	python scripts/add_unknown_words.py --dry-run

## Add unknown words to dictionary
dict-update: ## Add unknown words to dictionary
	python scripts/add_unknown_words.py

## Update domain dictionary with known terms
dict-domain: ## Update dictionary with domain-specific terms
	python scripts/update_domain_dictionary.py

## Smoke test (auto: 8000 then 8001)
smoke-auto: ## Try health+bmi on 8000 then 8001
	@if curl -fsS http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then \
		echo "Using 8000"; \
		bash ./scripts/smoke.sh http://127.0.0.1:8000; \
	elif curl -fsS http://127.0.0.1:8001/api/v1/health >/dev/null 2>&1; then \
		echo "Using 8001"; \
		bash ./scripts/smoke.sh http://127.0.0.1:8001; \
	else \
		echo "No server found on 8000/8001"; exit 1; \
	fi

## Smoke test on :8000
smoke-8000: ## Smoke against http://127.0.0.1:8000
	bash ./scripts/smoke.sh http://127.0.0.1:8000

## Smoke test on :8001
smoke-8001: ## Smoke against http://127.0.0.1:8001
	bash ./scripts/smoke.sh http://127.0.0.1:8001

## Build docker image
docker-build: ## docker build -t bmi-app:dev .
	docker build -t bmi-app:dev .

## Run docker (foreground) on :8000
docker-run: ## docker run --rm -p 8000:8000 bmi-app:dev
	docker run --rm -p 8000:8000 bmi-app:dev

## Run docker (background) on :8000
docker-run-bg: ## docker run -d --name bmi-app -p 8000:8000 bmi-app:dev
	docker run -d --name bmi-app -p 8000:8000 bmi-app:dev

## Stop & remove docker container
docker-stop: ## stop & remove container bmi-app
	- docker stop bmi-app 2>/dev/null || true
	- docker rm bmi-app 2>/dev/null || true

## Restart docker on :8001 (background)
docker-restart-8001: ## run -d --name bmi-app -p 8001:8000 bmi-app:dev
	- docker rm -f bmi-app 2>/dev/null || true
	docker run -d --name bmi-app -p 8001:8000 bmi-app:dev
	@echo "✅ Open: http://127.0.0.1:8001/docs"

.PHONY: help pre-commit-setup venv dev test cov cov-html lint fmt fmt-lines fmt-lines-dry line-check line-check-dry dict-dry-run dict-update dict-domain smoke-auto smoke-8000 smoke-8001 docker-build docker-run docker-run-bg docker-stop docker-restart-8001
