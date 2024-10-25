# Airflow instance running at localhost:8080
import os
from pathlib import Path

from dagster import AssetKey

# Migrating airflow instance
AIRFLOW_BASE_URL = "http://localhost:8080"
AIRFLOW_INSTANCE_NAME = "my_airflow_instance"

# Federated airflow instance
FEDERATED_BASE_URL = "http://localhost:8081"
FEDERATED_INSTANCE_NAME = "my_federated_airflow_instance"

# Authentication credentials (lol)
USERNAME = "admin"
PASSWORD = "admin"

ASSETS_PATH = Path(__file__).parent / "defs"
PROXIED_STATE_PATH = Path(__file__).parent / "proxied_state"
DBT_DAG_ASSET_KEY = AssetKey([AIRFLOW_INSTANCE_NAME, "dag", "dbt_dag"])
UPLOAD_SOURCE_DATA_ASSET_KEY = AssetKey([FEDERATED_INSTANCE_NAME, "dag", "upload_source_data"])
DBT_MODEL_TO_DAG = {"model.test_environment.cleaned_corpus": UPLOAD_SOURCE_DATA_ASSET_KEY}


def dbt_project_path() -> Path:
    env_val = os.getenv("DBT_PROJECT_DIR")
    assert env_val
    return Path(env_val)


def dbt_manifest_path() -> Path:
    return dbt_project_path() / "target" / "manifest.json"
