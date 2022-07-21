from dagster import DagsterInstance
from dagster._core.workspace import WorkspaceProcessContext
from dagster._core.workspace.load import load_workspace_process_context_from_yaml_paths
from dagster._utils import file_relative_path


def test_load_in_process_location_hello_world_terse():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [file_relative_path(__file__, "terse_python_module_workspace.yaml")],
    ) as workspace:
        assert isinstance(workspace, WorkspaceProcessContext)
        assert workspace.repository_locations_count == 1
        assert workspace.repository_location_names[0] == "dagster.utils.test.hello_world_repository"


def test_load_in_process_location_hello_world_nested():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [file_relative_path(__file__, "nested_python_module_workspace.yaml")],
    ) as workspace:
        assert isinstance(workspace, WorkspaceProcessContext)
        assert workspace.repository_locations_count == 1
        assert workspace.repository_location_names[0] == "dagster.utils.test.hello_world_repository"


def test_load_in_process_location_hello_world_nested_with_def():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [file_relative_path(__file__, "nested_with_def_python_module_workspace.yaml")],
    ) as workspace:
        assert isinstance(workspace, WorkspaceProcessContext)
        assert workspace.repository_locations_count == 1
        assert (
            workspace.repository_location_names[0]
            == "dagster.utils.test.hello_world_repository:hello_world_repository"
        )
