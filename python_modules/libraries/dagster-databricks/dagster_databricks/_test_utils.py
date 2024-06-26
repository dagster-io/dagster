import os

import pytest
from databricks.sdk import WorkspaceClient

DAGSTER_PIPES_WHL_FILENAME = "dagster_pipes-1!0+dev-py3-none-any.whl"

# This has been manually uploaded to a test DBFS workspace.
DAGSTER_PIPES_WHL_PATH = f"dbfs:/FileStore/jars/{DAGSTER_PIPES_WHL_FILENAME}"


def get_repo_root() -> str:
    path = os.path.dirname(__file__)
    while not os.path.exists(os.path.join(path, ".git")):
        path = os.path.dirname(path)
    return path


@pytest.fixture
def databricks_client() -> WorkspaceClient:
    return WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )

