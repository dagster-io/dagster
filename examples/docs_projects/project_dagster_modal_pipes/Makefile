ruff:
	ruff check --select I --fix .

clean:
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -exec rm -f {} +

install:
	uv pip install -e .[dev]
