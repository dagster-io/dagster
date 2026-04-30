import os
from collections.abc import Mapping
from typing import Any
from unittest.mock import MagicMock, patch

import dagster as dg
import pytest
from dagster import AssetsDefinition, SensorDefinition
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
    workspace.project_id = 123
    workspace.environment_id = 456
    workspace.credentials = MagicMock(account_id=999)
    workspace.fetch_workspace_data.return_value = mock_workspace_data
    workspace.get_or_fetch_workspace_data.return_value = mock_workspace_data

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


def test_dbt_cloud_component_create_sensor(tmp_path, mock_workspace, mock_workspace_data):
    """Test that create_sensor=True includes a SensorDefinition in the built defs."""
    component = DbtCloudComponent(
        workspace=mock_workspace,
        create_sensor=True,
        defs_state=DefsStateConfigArgs.local_filesystem(),
    )

    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    mock_load_context = MagicMock()
    defs = component.build_defs_from_state(mock_load_context, state_path)

    assets = list(defs.assets) if defs.assets else []
    assert len(assets) == 1
    assert isinstance(assets[0], AssetsDefinition)

    sensors = list(defs.sensors) if defs.sensors else []
    assert len(sensors) == 1
    assert isinstance(sensors[0], SensorDefinition)


def test_dbt_cloud_component_sensor_included_by_default(
    tmp_path, mock_workspace, mock_workspace_data
):
    """Test that create_sensor defaults to True and a sensor is included."""
    component = DbtCloudComponent(
        workspace=mock_workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
    )

    assert component.create_sensor is True

    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    mock_load_context = MagicMock()
    defs = component.build_defs_from_state(mock_load_context, state_path)

    sensors = list(defs.sensors) if defs.sensors else []
    assert len(sensors) == 1
    assert isinstance(sensors[0], SensorDefinition)


def test_dbt_cloud_component_from_yaml_with_sensor(mock_workspace_data):
    """Test that create_sensor can be set via YAML configuration."""
    body = {
        **BASIC_DBT_CLOUD_COMPONENT_BODY,
        "attributes": {
            **BASIC_DBT_CLOUD_COMPONENT_BODY["attributes"],
            "create_sensor": True,
        },
    }
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DbtCloudComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, _defs),
        ):
            assert isinstance(component, DbtCloudComponent)
            assert component.create_sensor is True


def test_dbt_cloud_component_translation_none_by_default(mock_workspace_data):
    """Test that translation is None by default and does not alter asset specs."""
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
            assert component.translation is None


def test_dbt_cloud_component_translation_group_name_yaml(mock_workspace_data):
    """Test that the translation YAML block is parsed and the resolved fn applies correctly."""
    body = {
        **BASIC_DBT_CLOUD_COMPONENT_BODY,
        "attributes": {
            **BASIC_DBT_CLOUD_COMPONENT_BODY["attributes"],
            "translation": {
                "group_name": "{{ node.fqn[1] if node.fqn|length > 1 else 'default' }}",
            },
        },
    }
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DbtCloudComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, _defs),
        ):
            assert isinstance(component, DbtCloudComponent)
            assert component.translation is not None

            # Call the resolved Jinja2 translation fn directly to verify it works
            # without hitting the real dbt Cloud API.
            base_spec = dg.AssetSpec(key=dg.AssetKey("my_model"))
            result = component.translation(base_spec, {"fqn": ["my_project", "my_model"]})
            assert result.group_name == "my_model"

            result_default = component.translation(base_spec, {"fqn": ["my_project"]})
            assert result_default.group_name == "default"


def test_dbt_cloud_component_translation_applies_to_asset_specs(
    tmp_path, mock_workspace, mock_workspace_data
):
    """Test that a translation fn is applied when building defs from state."""

    def my_translation(base_spec: dg.AssetSpec, dbt_props: Mapping[str, Any]) -> dg.AssetSpec:
        fqn = dbt_props.get("fqn", [])
        return base_spec.replace_attributes(group_name=fqn[1] if len(fqn) > 1 else "default")

    component = DbtCloudComponent(
        workspace=mock_workspace,
        translation=my_translation,
        defs_state=DefsStateConfigArgs.local_filesystem(),
    )

    state_path = tmp_path / "state.json"
    component.write_state_to_path(state_path)
    mock_load_context = MagicMock()
    defs = component.build_defs_from_state(mock_load_context, state_path)

    assets = list(defs.assets) if defs.assets else []
    assert len(assets) == 1
    assert isinstance(assets[0], AssetsDefinition)
    spec = next(iter(assets[0].specs))
    # fqn for "model.my_project.my_model" is ["my_project", "my_model"] -> fqn[1] = "my_model"
    assert spec.group_name == "my_model"


def test_dbt_cloud_component_subclass_get_asset_spec(tmp_path, mock_workspace, mock_workspace_data):
    """Test that a subclass can override get_asset_spec to customise asset specs."""

    class CustomDbtCloudComponent(DbtCloudComponent):
        def get_asset_spec(self, manifest, unique_id, project) -> dg.AssetSpec:
            base_spec = super().get_asset_spec(manifest, unique_id, project)
            return base_spec.replace_attributes(
                tags={**base_spec.tags, "custom_tag": "custom_value"}
            )

    component = CustomDbtCloudComponent(
        workspace=mock_workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
    )

    state_path = tmp_path / "state.json"
    component.write_state_to_path(state_path)
    mock_load_context = MagicMock()
    defs = component.build_defs_from_state(mock_load_context, state_path)

    assets = list(defs.assets) if defs.assets else []
    assert len(assets) == 1
    assert isinstance(assets[0], AssetsDefinition)
    spec = next(iter(assets[0].specs))
    assert spec.tags.get("custom_tag") == "custom_value"
