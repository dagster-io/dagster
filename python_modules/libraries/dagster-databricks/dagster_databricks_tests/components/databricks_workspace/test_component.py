import pytest
from unittest.mock import AsyncMock, patch

from dagster import AssetKey
from dagster.components.testing import create_defs_folder_sandbox
from dagster._utils.test.definitions import scoped_definitions_load_context

from dagster_databricks.components.databricks_asset_bundle.configs import Job
from dagster_databricks.components.databricks_workspace.component import DatabricksWorkspaceComponent

MOCK_JOBS_DATA = [
    Job(
        job_id=101,
        settings={"name": "Data Ingestion Job"},
        tasks=[{"task_key": "ingest_task", "description": "Ingests data"}]
    ),
    Job(
        job_id=102,
        settings={"name": "ML Training Job"},
        tasks=[
            {"task_key": "prepare_data", "description": "Prep"},
            {"task_key": "train_model", "description": "Train"}
        ]
    )
]

COMPONENT_YAML = {
    "type": "dagster_databricks.DatabricksWorkspaceComponent",
    "attributes": {
        "workspace": {
            "host": "https://fake-workspace.cloud.databricks.com",
            "token": "fake-token"
        },
        "databricks_filter": {
            "include_jobs": {
                "job_ids": [101, 102]
            }
        }
    }
}

@pytest.fixture
def mock_fetcher():
    with patch(
        "dagster_databricks.components.databricks_workspace.component.fetch_databricks_workspace_data",
        new_callable=AsyncMock
    ) as mock:
        mock.return_value = MOCK_JOBS_DATA
        yield mock

def test_databricks_workspace_loading(mock_fetcher):
    """Test that the component correctly loads jobs and converts them to assets."""
    
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DatabricksWorkspaceComponent,
            defs_yaml_contents=COMPONENT_YAML,
        )

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, DatabricksWorkspaceComponent)
            
            mock_fetcher.assert_called_once()
            
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()
            
            assert AssetKey(["ingest_task"]) in asset_keys
            
            assert AssetKey(["prepare_data"]) in asset_keys
            
            assert AssetKey(["train_model"]) in asset_keys
            
            assert len(asset_keys) == 3