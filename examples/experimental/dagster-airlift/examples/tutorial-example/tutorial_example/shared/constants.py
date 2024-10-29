import os
from pathlib import Path


def data_dir() -> Path:
    return Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "data"


CUSTOMERS_CSV_PATH = data_dir() / "customers.csv"
WAREHOUSE_PATH = data_dir() / "jaffle_shop.duckdb"
