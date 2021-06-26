from dagster.core.workspace import Workspace
from dagster.core.workspace.load import load_workspace_from_yaml_paths
from dagster.utils import file_relative_path


def test_load_in_process_location_hello_world_terse():
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "terse_python_module_workspace.yaml")],
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert workspace.repository_locations_count == 1
        assert workspace.repository_location_names[0] == "dagster.utils.test.hello_world_repository"


def test_load_in_process_location_hello_world_nested():
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "nested_python_module_workspace.yaml")],
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert workspace.repository_locations_count == 1
        assert workspace.repository_location_names[0] == "dagster.utils.test.hello_world_repository"


def test_load_in_process_location_hello_world_nested_with_def():
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "nested_with_def_python_module_workspace.yaml")],
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert workspace.repository_locations_count == 1
        assert (
            workspace.repository_location_names[0]
            == "dagster.utils.test.hello_world_repository:hello_world_repository"
        )
