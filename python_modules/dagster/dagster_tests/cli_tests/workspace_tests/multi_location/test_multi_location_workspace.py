import sys

import yaml

from dagster.api.snapshot_repository import sync_get_external_repositories
from dagster.cli.workspace import Workspace
from dagster.cli.workspace.load import load_workspace_from_config, load_workspace_from_yaml_paths
from dagster.utils import file_relative_path


def test_multi_location_workspace():
    workspace = load_workspace_from_yaml_paths(
        [file_relative_path(__file__, 'multi_location.yaml')]
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 2
    assert workspace.has_repository_location_handle('loaded_from_file')
    assert workspace.has_repository_location_handle('loaded_from_module')


def test_multi_file_extend_workspace():
    workspace = load_workspace_from_yaml_paths(
        [
            file_relative_path(__file__, 'multi_location.yaml'),
            file_relative_path(__file__, 'extra_location.yaml'),
        ]
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 3
    assert workspace.has_repository_location_handle('loaded_from_file')
    assert workspace.has_repository_location_handle('loaded_from_module')
    assert workspace.has_repository_location_handle('extra_location')


def test_multi_file_override_workspace():
    workspace = load_workspace_from_yaml_paths(
        [
            file_relative_path(__file__, 'multi_location.yaml'),
            file_relative_path(__file__, 'override_location.yaml'),
        ]
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 2
    assert workspace.has_repository_location_handle('loaded_from_file')
    assert workspace.has_repository_location_handle('loaded_from_module')

    # Ensure location `loaded_from_file` has been overridden
    external_repositories = sync_get_external_repositories(
        workspace.get_repository_location_handle('loaded_from_file')
    )
    assert len(external_repositories) == 1
    assert external_repositories[0].name == "extra_repository"


def test_multi_file_extend_and_override_workspace():
    workspace = load_workspace_from_yaml_paths(
        [
            file_relative_path(__file__, 'multi_location.yaml'),
            file_relative_path(__file__, 'override_location.yaml'),
            file_relative_path(__file__, 'extra_location.yaml'),
        ]
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 3
    assert workspace.has_repository_location_handle('loaded_from_file')
    assert workspace.has_repository_location_handle('loaded_from_module')
    assert workspace.has_repository_location_handle('extra_location')

    # Ensure location `loaded_from_file` has been overridden
    external_repositories = sync_get_external_repositories(
        workspace.get_repository_location_handle('loaded_from_file')
    )
    assert len(external_repositories) == 1
    assert external_repositories[0].name == "extra_repository"


def test_multi_python_environment_workspace():
    workspace_yaml = '''
load_from:
    - python_environment:
        executable_path: {executable}
        target:
            python_file:
                relative_path: hello_world_repository.py
                location_name: loaded_from_file

    - python_environment:
        executable_path: {executable}
        target:
            python_module:
                module_name: dagster.utils.test.hello_world_repository
                location_name: loaded_from_module

    '''.format(
        executable=sys.executable
    )

    workspace = load_workspace_from_config(
        yaml.safe_load(workspace_yaml),
        # fake out as if it were loaded by a yaml file in this directory
        file_relative_path(__file__, 'not_a_real.yaml'),
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 2
    assert workspace.has_repository_location_handle('loaded_from_file')
    assert workspace.has_repository_location_handle('loaded_from_module')

    loaded_from_file_handle = workspace.get_repository_location_handle('loaded_from_file')
    assert set(loaded_from_file_handle.repository_code_pointer_dict.keys()) == {
        'hello_world_repository'
    }

    loaded_from_module_handle = workspace.get_repository_location_handle('loaded_from_module')
    assert set(loaded_from_module_handle.repository_code_pointer_dict.keys()) == {
        'hello_world_repository'
    }
