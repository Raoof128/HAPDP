PYTHON ?= python3
APP_MODULE ?= main:app

.PHONY: install dev-install lint format test run mock-ai docker-build docker-up docker-down pre-commit

install:
$(PYTHON) -m pip install --upgrade pip
$(PYTHON) -m pip install -r requirements.txt

dev-install:
$(PYTHON) -m pip install --upgrade pip
$(PYTHON) -m pip install -r requirements-dev.txt

lint:
ruff check .

format:
black .

test:
    pytest

pre-commit:
    pre-commit run --all-files

run:
uvicorn $(APP_MODULE) --host 0.0.0.0 --port 8000 --reload

mock-ai:
$(PYTHON) scripts/mock_ai.py

docker-build:
docker build -t fhir-privacy-proxy .

docker-up:
docker compose up --build

docker-down:
docker compose down
