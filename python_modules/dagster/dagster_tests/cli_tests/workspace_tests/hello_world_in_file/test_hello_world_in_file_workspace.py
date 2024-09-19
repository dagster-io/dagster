import pytest
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load import load_workspace_process_context_from_yaml_paths
from dagster._utils import file_relative_path


@pytest.fixture
def instance():
    with instance_for_test() as instance:
        yield instance


def get_hello_world_path():
    return file_relative_path(__file__, "hello_world_repository.py")


def test_load_in_process_location_hello_world_nested_no_def(instance):
    file_name = file_relative_path(__file__, "nested_python_file_workspace.yaml")
    with load_workspace_process_context_from_yaml_paths(
        instance, [file_name]
    ) as workspace_process_context:
        assert isinstance(workspace_process_context, WorkspaceProcessContext)
        assert workspace_process_context.code_locations_count == 1
        assert workspace_process_context.code_location_names[0] == "hello_world_repository.py"


def test_load_in_process_location_hello_world_nested_with_def(instance):
    file_name = file_relative_path(__file__, "nested_with_def_python_file_workspace.yaml")
    with load_workspace_process_context_from_yaml_paths(
        instance, [file_name]
    ) as workspace_process_context:
        assert isinstance(workspace_process_context, WorkspaceProcessContext)
        assert workspace_process_context.code_locations_count == 1
        assert (
            workspace_process_context.code_location_names[0]
            == "hello_world_repository.py:hello_world_repository"
        )


def test_load_in_process_location_hello_world_terse(instance):
    file_name = file_relative_path(__file__, "terse_python_file_workspace.yaml")

    with load_workspace_process_context_from_yaml_paths(
        instance, [file_name]
    ) as workspace_process_context:
        assert isinstance(workspace_process_context, WorkspaceProcessContext)
        assert workspace_process_context.code_locations_count == 1
        assert workspace_process_context.code_location_names[0] == "hello_world_repository.py"
