from pathlib import Path

import pytest
from dagster_databricks.components.databricks_asset_bundle.databricks_configs import (
    DatabricksConfigs,
)

DATABRICKS_CONFIGS_LOCATION_PATH = Path(__file__).parent / "configs" / "databricks.yml"


def test_load_databricks_configs():
    # Task dataclasses are not implemented yet, no task is parsed so an exception is raised
    with pytest.raises(ValueError, match="No tasks found in databricks config"):
        DatabricksConfigs(databricks_configs_path=DATABRICKS_CONFIGS_LOCATION_PATH)
