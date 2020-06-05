from dagster.cli.workspace import Workspace
from dagster.cli.workspace.load import load_workspace_from_yaml_path
from dagster.utils import file_relative_path


def test_multi_location_workspace():
    workspace = load_workspace_from_yaml_path(file_relative_path(__file__, 'multi_location.yaml'))
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 2
    assert workspace.has_repository_location_handle('loaded_from_file')
    assert workspace.has_repository_location_handle('loaded_from_module')
