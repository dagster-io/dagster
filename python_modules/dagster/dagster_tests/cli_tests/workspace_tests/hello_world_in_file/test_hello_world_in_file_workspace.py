from dagster import DagsterInstance
from dagster._utils import file_relative_path
from dagster._core.workspace import WorkspaceProcessContext
from dagster._core.workspace.load import load_workspace_process_context_from_yaml_paths


def get_hello_world_path():
    return file_relative_path(__file__, "hello_world_repository.py")


def test_load_in_process_location_hello_world_nested_no_def():
    file_name = file_relative_path(__file__, "nested_python_file_workspace.yaml")
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_name]
    ) as workspace_process_context:
        assert isinstance(workspace_process_context, WorkspaceProcessContext)
        assert workspace_process_context.repository_locations_count == 1
        assert workspace_process_context.repository_location_names[0] == "hello_world_repository.py"


def test_load_in_process_location_hello_world_nested_with_def():
    file_name = file_relative_path(__file__, "nested_with_def_python_file_workspace.yaml")
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_name]
    ) as workspace_process_context:
        assert isinstance(workspace_process_context, WorkspaceProcessContext)
        assert workspace_process_context.repository_locations_count == 1
        assert (
            workspace_process_context.repository_location_names[0]
            == "hello_world_repository.py:hello_world_repository"
        )


def test_load_in_process_location_hello_world_terse():
    file_name = file_relative_path(__file__, "terse_python_file_workspace.yaml")

    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_name]
    ) as workspace_process_context:
        assert isinstance(workspace_process_context, WorkspaceProcessContext)
        assert workspace_process_context.repository_locations_count == 1
        assert workspace_process_context.repository_location_names[0] == "hello_world_repository.py"
