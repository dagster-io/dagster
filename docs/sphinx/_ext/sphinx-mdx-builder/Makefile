install:
	uv pip install -e .

install_dev: install
	uv pip install -e .[test]

lint:
	ruff format .
	ruff check --fix 

lint_check:
	ruff check
	ruff format --check

ruff:
	$(MAKE) -C ../../../.. ruff

test:
	pytest -v
