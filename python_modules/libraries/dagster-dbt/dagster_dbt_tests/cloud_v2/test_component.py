import os
from unittest.mock import MagicMock, patch

import pytest
from dagster import AssetsDefinition
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.resolved.context import ResolutionContext
from dagster.components.testing import create_defs_folder_sandbox
from dagster.components.utils.defs_state import DefsStateConfigArgs
from dagster_dbt.cloud_v2.component.dbt_cloud_component import DbtCloudComponent
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.cloud_v2.types import DbtCloudWorkspaceData
from dagster_dbt.components.dbt_component_utils import _set_resolution_context


@pytest.fixture
def mock_workspace_data():
    """Create dummy data mimicking dbt Cloud API response."""
    return DbtCloudWorkspaceData(
        project_id=123,
        environment_id=456,
        adhoc_job_id=789,
        manifest={
            "metadata": {
                "dbt_schema_version": "1.0.0",
                "adapter_type": "postgres",
            },
            "nodes": {
                "model.my_project.my_model": {
                    "resource_type": "model",
                    "package_name": "my_project",
                    "path": "my_model.sql",
                    "original_file_path": "models/my_model.sql",
                    "unique_id": "model.my_project.my_model",
                    "fqn": ["my_project", "my_model"],
                    "name": "my_model",
                    "config": {"enabled": True},
                    "tags": [],
                    "depends_on": {"nodes": []},
                    "description": "A test model",
                }
            },
            "sources": {},
            "metrics": {},
            "semantic_models": {},
            "exposures": {},
            "checks": {},
            "child_map": {"model.my_project.my_model": []},
            "parent_map": {"model.my_project.my_model": []},
            "selectors": {},
        },
        jobs=[
            {
                "id": 789,
                "account_id": 111,
                "name": "Adhoc Job",
                "environment_id": 456,
                "project_id": 123,
            }
        ],
    )


@pytest.fixture
def mock_workspace(mock_workspace_data):
    """Mock the DbtCloudWorkspace resource."""
    workspace = MagicMock(spec=DbtCloudWorkspace)
    workspace.unique_id = "123-456"
    workspace.fetch_workspace_data.return_value = mock_workspace_data

    mock_invocation = MagicMock()
    mock_invocation.wait.return_value = []
    workspace.cli.return_value = mock_invocation

    return workspace


def test_dbt_cloud_component_state_cycle(tmp_path, mock_workspace, mock_workspace_data):
    """Test 1: Full cycle - Write State -> Read State -> Build Defs."""
    component = DbtCloudComponent(
        workspace=mock_workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
    )

    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    assert state_path.exists()

    mock_load_context = MagicMock()
    defs = component.build_defs_from_state(mock_load_context, state_path)

    assets = list(defs.assets) if defs.assets else []
    assert len(assets) == 1

    asset_def = assets[0]
    assert isinstance(asset_def, AssetsDefinition)
    assert asset_def.node_def.name == "dbt_cloud_assets"


def test_dbt_cloud_component_execution(mock_workspace):
    """Test 2: Execution calls the workspace CLI correctly with configured args."""
    component = DbtCloudComponent(
        workspace=mock_workspace, cli_args=["build", "--select", "tag:staging"]
    )

    context = MagicMock()
    context.has_partition_key = False
    context.has_partition_key_range = False

    dummy_resolution_context = ResolutionContext.default()

    with _set_resolution_context(dummy_resolution_context):
        iterator = component.execute(context)
        list(iterator)

    mock_workspace.cli.assert_called_once()
    call_args = mock_workspace.cli.call_args[1]
    assert call_args["args"] == ["build", "--select", "tag:staging"]


BASIC_DBT_CLOUD_COMPONENT_BODY = {
    "type": "dagster_dbt.DbtCloudComponent",
    "attributes": {
        "workspace": {
            "account_id": 123456,
            "token": "test-token",
            "access_url": "https://cloud.getdbt.com",
            "project_id": 11111,
            "environment_id": 22222,
        },
        "select": "tag:dagster",
    },
}


def test_dbt_cloud_component_from_yaml(mock_workspace_data):
    """Test that DbtCloudComponent can be loaded from YAML configuration."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DbtCloudComponent,
            defs_yaml_contents=BASIC_DBT_CLOUD_COMPONENT_BODY,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, _defs),
        ):
            assert isinstance(component, DbtCloudComponent)
            assert isinstance(component.workspace, DbtCloudWorkspace)
            assert component.workspace.credentials.account_id == 123456
            assert component.workspace.credentials.token == "test-token"
            assert component.workspace.credentials.access_url == "https://cloud.getdbt.com"
            assert component.workspace.project_id == 11111
            assert component.workspace.environment_id == 22222
            assert component.select == "tag:dagster"


def test_dbt_cloud_component_from_yaml_with_env_vars(mock_workspace_data):
    """Test that DbtCloudComponent resolves Jinja env var templates from YAML."""
    body = {
        "type": "dagster_dbt.DbtCloudComponent",
        "attributes": {
            "workspace": {
                "account_id": 123456,
                "token": "{{ env.DBT_CLOUD_TOKEN }}",
                "project_id": 11111,
                "environment_id": 22222,
            },
        },
    }
    with (
        patch.dict(os.environ, {"DBT_CLOUD_TOKEN": "my-secret-token"}),
        create_defs_folder_sandbox() as sandbox,
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=DbtCloudComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, _defs),
        ):
            assert isinstance(component, DbtCloudComponent)
            assert component.workspace.credentials.token == "my-secret-token"
