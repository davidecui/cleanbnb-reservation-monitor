.PHONY: setup run-local test lint build

setup:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt

run-local:
	python -m app.main

test:
	pytest -v tests/

lint:
	black app/ tests/
	flake8 app/ tests/

build:
	docker build -t cleanbnb-monitor .
