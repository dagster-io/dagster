.PHONY: install lint fix test webserver

install:
	pip install --upgrade uv
	uv pip install -e .[dev]

lint:
	ruff check .
	ruff format --check .

fix:
	ruff check --fix .
	ruff format .

test:
	pytest 

webserver:
	python -m webserver.main
