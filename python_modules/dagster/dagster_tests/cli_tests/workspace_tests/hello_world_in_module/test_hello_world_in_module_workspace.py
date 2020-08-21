import pytest

from dagster.cli.workspace import Workspace
from dagster.cli.workspace.load import load_workspace_from_yaml_paths
from dagster.core.host_representation.handle import UserProcessApi
from dagster.utils import file_relative_path


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_load_in_process_location_handle_hello_world_terse(python_user_process_api):
    workspace = load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "terse_python_module_workspace.yaml")],
        python_user_process_api,
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 1


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_load_in_process_location_handle_hello_world_nested(python_user_process_api):
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "nested_python_module_workspace.yaml")],
        python_user_process_api,
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 1


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_load_in_process_location_handle_hello_world_nested_with_def(python_user_process_api):
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "nested_with_def_python_module_workspace.yaml")],
        python_user_process_api,
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 1
