import json
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
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


@pytest.fixture
def mock_databricks_cli_resolved_config():
    """Returns a mock resolved configuration as would be returned by `databricks bundle validate --output json`.

    This simulates the Databricks CLI resolving all template variables like ${workspace.current_user.userName}.
    """
    # Load the raw YAML configs
    with open(DATABRICKS_CONFIG_LOCATION_PATH) as f:
        databricks_config = yaml.safe_load(f)

    jobs_yml_path = DATABRICKS_CONFIG_LOCATION_PATH.parent / "resources" / "jobs.yml"
    with open(jobs_yml_path) as f:
        jobs_config = yaml.safe_load(f)

    # Simulate resolved configuration with template variables expanded
    resolved_config = {
        "bundle": databricks_config.get("bundle", {}),
        "variables": databricks_config.get("variables", {}),
        "resources": {"jobs": {}},
    }

    # Process jobs and resolve template variables
    for job_name, job_config in jobs_config.get("resources", {}).get("jobs", {}).items():
        resolved_job_config = {"name": job_config.get("name", job_name), "tasks": []}

        # Copy job-level parameters
        if "parameters" in job_config:
            resolved_job_config["parameters"] = job_config["parameters"]

        # Process tasks and resolve template variables
        for task in job_config.get("tasks", []):
            resolved_task = dict(task)

            # Resolve ${workspace.current_user.userName} in notebook_path
            if "notebook_task" in resolved_task:
                notebook_task = dict(resolved_task["notebook_task"])
                if "notebook_path" in notebook_task:
                    # Simulate resolution of Databricks template variables
                    notebook_path = notebook_task["notebook_path"]
                    notebook_path = notebook_path.replace(
                        "${workspace_user}", "test_user@example.com"
                    )
                    notebook_path = notebook_path.replace(
                        "{{workspace_user}}", "test_user@example.com"
                    )
                    notebook_task["notebook_path"] = notebook_path
                resolved_task["notebook_task"] = notebook_task

            resolved_job_config["tasks"].append(resolved_task)

        resolved_config["resources"]["jobs"][job_name] = resolved_job_config

    return resolved_config


@pytest.fixture(autouse=True)
def mock_databricks_cli(mock_databricks_cli_resolved_config):
    """Auto-use fixture that mocks the Databricks CLI subprocess call."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps(mock_databricks_cli_resolved_config)
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        yield mock_run
