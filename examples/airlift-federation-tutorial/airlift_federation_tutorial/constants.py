from pathlib import Path

FEDERATION_TUTORIAL_ROOT_DIR = Path(__file__).parent.parent
DUCKDB_PATH = FEDERATION_TUTORIAL_ROOT_DIR / "federation_tutorial.db"

CUSTOMERS_CSV_PATH = FEDERATION_TUTORIAL_ROOT_DIR / "raw_customers.csv"
CUSTOMERS_COLS = [
    "id",
    "first_name",
    "last_name",
]
CUSTOMERS_SCHEMA = "raw_data"
CUSTOMERS_DB_NAME = "federation_tutorial"
CUSTOMERS_TABLE_NAME = "raw_customers"
METRICS_SCHEMA = "metrics"
METRICS_TABLE_NAME = "customer_count"
