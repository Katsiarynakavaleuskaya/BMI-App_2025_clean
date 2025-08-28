.PHONY: run test cov kill health dev tunnel smoke stop dev-all stop-all tunnel-bg tunnel-stop tunnel-url smoke-ext

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

stop:
	@echo "Stopping uvicorn on port 8001..."
	@lsof -ti :8001 | xargs -r kill -9 || true

dev:
	conda activate bmi_fix && cd ~/BMI-App_2025_clean && uvicorn app:app --host 127.0.0.1 --port 8001 --reload

tunnel:
	npx localtunnel --port 8001 --local-host 127.0.0.1 --print-requests

smoke:
	curl -s http://127.0.0.1:8001/health || echo "health failed"; \
	curl -s -X POST http://127.0.0.1:8001/bmi -H "Content-Type: application/json" \
	-d '{"height_m":1.70,"weight_kg":65,"age":28,"gender":"female","pregnant":"no","athlete":"no","user_group":"general","language":"en"}' || echo "bmi failed"

dev-all:
	( nohup conda run -n bmi_fix uvicorn app:app --host 127.0.0.1 --port 8001 --reload > uvicorn.out 2>&1 & echo $$! > uvicorn.pid )
	sleep 2
	$(MAKE) smoke

stop-all:
	[ -f uvicorn.pid ] && kill -9 $$(cat uvicorn.pid) 2>/dev/null || true
	rm -f uvicorn.pid uvicorn.out
	$(MAKE) stop

tunnel-bg:
	( nohup npx localtunnel --port 8001 --local-host 127.0.0.1 --print-requests > tunnel.out 2>&1 & echo $$! > tunnel.pid )

tunnel-stop:
	rm -f tunnel.out tunnel.pid
	$(MAKE) tunnel-bg
	sleep 2
	ls -l tunnel.out tunnel.pid
	tail -n 10 tunnel.out

tunnel-url:
	@grep -o 'https://[a-zA-Z0-9.-]*\.loca\.lt' tunnel.out | tail -n 1 || echo "no url yet"

smoke-ext:
	@URL="$$(make -s tunnel-url)"; \
	if [ "$$URL" = "no url yet" ]; then echo "no tunnel url"; exit 1; fi; \
	echo "Testing API at $$URL"; \
	curl -s "$$URL/health" || echo "health failed"; \
	curl -s -X POST "$$URL/bmi" \
	  -H "Content-Type: application/json" \
	  -d '{"height_m":1.70,"weight_kg":65,"age":28,"gender":"female","pregnant":"no","athlete":"no","user_group":"general","language":"en"}' \
	  || echo "bmi failed"

.PHONY: smoke-bodyfat smoke-bodyfat-ext

smoke-bodyfat:
	./smoke_bodyfat.sh

smoke-bodyfat-ext:
	./smoke_bodyfat.sh --external

# --- Cloudflare quick tunnel helpers ---
.PHONY: cf-start cf-url cf-stop smoke-ext-bmi smoke-ext-bodyfat

# Запуск быстрого туннеля (без аккаунта), логи в tunnel.log
cf-start:
	cloudflared tunnel --url http://127.0.0.1:8001 --logfile tunnel.log --no-autoupdate & echo $$! > tunnel.pid; \
	sleep 2; $(MAKE) cf-url

# Достать URL из логов
cf-url:
	@grep -o 'https://[a-zA-Z0-9.-]*\.trycloudflare\.com' tunnel.log | tail -n 1 || echo "no-url"

# Остановить туннель
cf-stop:
	@[ -f tunnel.pid ] && kill -9 $$(cat tunnel.pid) 2>/dev/null || true; \
	rm -f tunnel.pid

# Внешний smoke для /bmi через Cloudflare URL
smoke-ext-bmi:
	@URL="$$( $(MAKE) -s cf-url )"; \
	if [ "$$URL" = "no-url" ] || [ -z "$$URL" ]; then echo "no tunnel url"; exit 1; fi; \
	echo "Testing BMI at $$URL"; \
	curl -s "$$URL/health" || echo "health failed"; \
	curl -s -X POST "$$URL/bmi" \
	  -H "Content-Type: application/json" \
	  -d '{"height_m":1.70,"weight_kg":65,"age":28,"gender":"female","pregnant":"no","athlete":"no","user_group":"general","language":"en"}' \
	  || echo "bmi failed"

# Внешний smoke для /bodyfat через Cloudflare URL
smoke-ext-bodyfat:
	@URL="$$( $(MAKE) -s cf-url )"; \
	if [ "$$URL" = "no-url" ] || [ -z "$$URL" ]; then echo "no tunnel url"; exit 1; fi; \
	echo "Testing BODYFAT at $$URL"; \
	curl -s -X POST "$$URL/bodyfat" \
	  -H "Content-Type: application/json" \
	  -d '{"height_m":1.70,"weight_kg":65,"age":28,"gender":"female","neck_cm":34,"waist_cm":74,"hip_cm":94}' \
	  | jq .
