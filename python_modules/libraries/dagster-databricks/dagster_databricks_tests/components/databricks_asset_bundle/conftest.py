import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

DATABRICKS_CONFIG_LOCATION_PATH = Path(__file__).parent / "configs" / "databricks.yml"

TEST_DATABRICKS_WORKSPACE_HOST = "test_host"
TEST_DATABRICKS_WORKSPACE_TOKEN = "test_token"


@pytest.fixture(scope="module")
def databricks_config_path() -> Iterator[str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(DATABRICKS_CONFIG_LOCATION_PATH.parent.parent, temp_dir, dirs_exist_ok=True)
        databricks_config_path = f"{temp_dir}/configs/databricks.yml"
        yield databricks_config_path


@pytest.fixture(scope="module")
def custom_config_path() -> Iterator[str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(CUSTOM_CONFIG_LOCATION_PATH.parent.parent, temp_dir, dirs_exist_ok=True)
        custom_config_path = f"{temp_dir}/configs/custom.yml"
        yield custom_config_path
