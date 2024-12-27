# Airflow instance running at localhost:8080
import os
from pathlib import Path

from dagster import AssetKey

# Migrating airflow instance
AIRFLOW_BASE_URL = "http://localhost:8080"
AIRFLOW_INSTANCE_NAME = "my_airflow_instance"

# Federated airflow instance
OTHER_TEAM_FEDERATED_BASE_URL = "http://localhost:8081"
LEGACY_FEDERATED_BASE_URL = "http://localhost:8082"
OTHER_TEAM_FEDERATED_INSTANCE_NAME = "other_team_instance"
LEGACY_FEDERATED_INSTANCE_NAME = "legacy_instance"

# Authentication credentials (lol)
USERNAME = "admin"
PASSWORD = "admin"

ASSETS_PATH = Path(__file__).parent / "defs"
PROXIED_STATE_PATH = Path(__file__).parent / "proxied_state"
DBT_DAG_ASSET_KEY = AssetKey([AIRFLOW_INSTANCE_NAME, "dag", "dbt_dag"])
UPLOAD_SOURCE_DATA_ASSET_KEY = AssetKey(
    [OTHER_TEAM_FEDERATED_INSTANCE_NAME, "dag", "upload_source_data"]
)
LEGACY_DAG_UPLOAD_ASSET_KEY = AssetKey([LEGACY_FEDERATED_INSTANCE_NAME, "dag", "upload_raw_iris"])
DBT_SOURCE_TO_DAG = {
    AssetKey("raw_customers"): UPLOAD_SOURCE_DATA_ASSET_KEY,
    AssetKey("raw_orders"): UPLOAD_SOURCE_DATA_ASSET_KEY,
    AssetKey("raw_payments"): UPLOAD_SOURCE_DATA_ASSET_KEY,
}
DBT_UPSTREAMS = {
    "model.test_environment.customer_metrics": AssetKey("customers"),
    "model.test_environment.order_metrics": AssetKey("orders"),
}
LAKEHOUSE_DEPS = {AssetKey(["lakehouse", "iris"]): [LEGACY_DAG_UPLOAD_ASSET_KEY]}


def dbt_project_path() -> Path:
    env_val = os.getenv("DBT_PROJECT_DIR")
    assert env_val
    return Path(env_val)


def dbt_manifest_path() -> Path:
    return dbt_project_path() / "target" / "manifest.json"
