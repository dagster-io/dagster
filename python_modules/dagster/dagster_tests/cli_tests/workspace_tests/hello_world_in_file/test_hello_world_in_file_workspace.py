from dagster.cli.workspace import Workspace
from dagster.cli.workspace.load import load_workspace_from_yaml_path
from dagster.seven import mock
from dagster.utils import file_relative_path


def get_hello_world_path():
    return file_relative_path(__file__, 'hello_world_repository.py')


def test_load_in_process_location_handle_hello_world_nested_no_def():
    workspace = load_workspace_from_yaml_path(
        file_relative_path(__file__, 'nested_python_file_workspace.yaml')
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 1
    assert workspace.repository_location_handles[0].location_name == 'hello_world_repository'


def test_load_in_process_location_handle_hello_world_nested_with_def():
    workspace = load_workspace_from_yaml_path(
        file_relative_path(__file__, 'nested_with_def_python_file_workspace.yaml')
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 1
    assert workspace.repository_location_handles[0].location_name == 'hello_world_repository'


def test_load_in_process_location_handle_hello_world_terse():
    workspace = load_workspace_from_yaml_path(
        file_relative_path(__file__, 'terse_python_file_workspace.yaml')
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 1
    assert workspace.repository_location_handles[0].location_name == 'hello_world_repository'


def test_load_in_process_location_handle_hello_world_through_legacy_codepath():
    workspace = load_workspace_from_yaml_path(
        file_relative_path(__file__, 'terse_python_file_workspace.yaml')
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 1


def test_load_legacy_repository_yaml():
    with mock.patch('warnings.warn') as warn_mock:
        workspace = load_workspace_from_yaml_path(
            file_relative_path(__file__, 'legacy_repository.yaml')
        )
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 1

        warn_mock.assert_called_once_with(
            'You are using the legacy repository yaml format. Please update your file '
            'to abide by the new workspace file format.'
        )
