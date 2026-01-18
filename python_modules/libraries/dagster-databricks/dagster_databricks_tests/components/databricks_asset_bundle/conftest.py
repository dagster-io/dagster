import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from dagster_databricks.components.databricks_asset_bundle.configs import (
    ResolvedDatabricksExistingClusterConfig,
    ResolvedDatabricksNewClusterConfig,
    ResolvedDatabricksServerlessConfig,
)

DATABRICKS_CONFIG_LOCATION_PATH = Path(__file__).parent / "configs" / "databricks.yml"

TEST_DATABRICKS_WORKSPACE_HOST = "test_host"
TEST_DATABRICKS_WORKSPACE_TOKEN = "test_token"


NEW_CLUSTER_CONFIG = {
    "spark_version": "test_spark_version",
    "node_type_id": "test_node_type_id",
    "num_workers": 2,
}
RESOLVED_NEW_CLUSTER_CONFIG = ResolvedDatabricksNewClusterConfig(**NEW_CLUSTER_CONFIG)

INVALID_PARTIAL_NEW_CLUSTER_CONFIG = {"spark_version": "test_spark_version"}


EXISTING_CLUSTER_CONFIG = {
    "existing_cluster_id": "test_existing_cluster_id",
}
RESOLVED_EXISTING_CLUSTER_CONFIG = ResolvedDatabricksExistingClusterConfig(
    **EXISTING_CLUSTER_CONFIG
)


SERVERLESS_CONFIG = {
    "is_serverless": True,
}
RESOLVED_SERVERLESS_CONFIG = ResolvedDatabricksServerlessConfig(**SERVERLESS_CONFIG)


@pytest.fixture(scope="module")
def databricks_config_path() -> Iterator[str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(DATABRICKS_CONFIG_LOCATION_PATH.parent.parent, temp_dir, dirs_exist_ok=True)
        databricks_config_path = f"{temp_dir}/configs/databricks.yml"
        yield databricks_config_path
