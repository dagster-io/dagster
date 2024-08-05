# Airflow instance running at localhost:8080
from pathlib import Path

AIRFLOW_BASE_URL = "http://localhost:8080"
AIRFLOW_INSTANCE_NAME = "my_airflow_instance"

# Authentication credentials (lol)
USERNAME = "admin"
PASSWORD = "admin"

ASSETS_PATH = Path(__file__).parent / "defs"
MIGRATION_STATE_PATH = Path(__file__).parent / "migration"
