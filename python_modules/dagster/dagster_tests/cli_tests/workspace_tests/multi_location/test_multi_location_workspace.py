import sys

import pytest
import yaml

from dagster.api.snapshot_repository import sync_get_external_repositories
from dagster.cli.workspace import Workspace
from dagster.cli.workspace.load import load_workspace_from_config, load_workspace_from_yaml_paths
from dagster.core.host_representation.handle import (
    ManagedGrpcPythonEnvRepositoryLocationHandle,
    PythonEnvRepositoryLocationHandle,
    UserProcessApi,
)
from dagster.utils import file_relative_path


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_multi_location_workspace(python_user_process_api):
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, 'multi_location.yaml')], python_user_process_api,
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 2
        assert workspace.has_repository_location_handle('loaded_from_file')
        assert workspace.has_repository_location_handle('loaded_from_module')


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_multi_file_extend_workspace(python_user_process_api):
    with load_workspace_from_yaml_paths(
        [
            file_relative_path(__file__, 'multi_location.yaml'),
            file_relative_path(__file__, 'extra_location.yaml'),
        ],
        python_user_process_api,
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 3
        assert workspace.has_repository_location_handle('loaded_from_file')
        assert workspace.has_repository_location_handle('loaded_from_module')
        assert workspace.has_repository_location_handle('extra_location')


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_multi_file_override_workspace(python_user_process_api):
    with load_workspace_from_yaml_paths(
        [
            file_relative_path(__file__, 'multi_location.yaml'),
            file_relative_path(__file__, 'override_location.yaml'),
        ],
        python_user_process_api,
    ) as workspace:
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


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_multi_file_extend_and_override_workspace(python_user_process_api):
    with load_workspace_from_yaml_paths(
        [
            file_relative_path(__file__, 'multi_location.yaml'),
            file_relative_path(__file__, 'override_location.yaml'),
            file_relative_path(__file__, 'extra_location.yaml'),
        ],
        python_user_process_api,
    ) as workspace:
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


def _get_multi_location_workspace_yaml():
    return '''
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

    - python_environment:
        executable_path: {executable}
        target:
            python_file:
                relative_path: named_hello_world_repository.py
                location_name: named_loaded_from_file

    - python_environment:
        executable_path: {executable}
        target:
            python_module:
                module_name: dagster.utils.test.named_hello_world_repository
                location_name: named_loaded_from_module

    - python_environment:
        executable_path: {executable}
        target:
            python_module:
                module_name: dagster.utils.test.named_hello_world_repository
                attribute: named_hello_world_repository
                location_name: named_loaded_from_module_attribute

    - python_environment:
        executable_path: {executable}
        target:
            python_file:
                relative_path: named_hello_world_repository.py
                attribute: named_hello_world_repository
                location_name: named_loaded_from_file_attribute

    '''.format(
        executable=sys.executable
    )


def test_multi_python_environment_workspace():
    with load_workspace_from_config(
        yaml.safe_load(_get_multi_location_workspace_yaml()),
        # fake out as if it were loaded by a yaml file in this directory
        file_relative_path(__file__, 'not_a_real.yaml'),
        UserProcessApi.CLI,
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 6
        assert workspace.has_repository_location_handle('loaded_from_file')
        assert workspace.has_repository_location_handle('loaded_from_module')
        assert workspace.has_repository_location_handle('named_loaded_from_file')
        assert workspace.has_repository_location_handle('named_loaded_from_module')

        loaded_from_file_handle = workspace.get_repository_location_handle('loaded_from_file')
        assert set(loaded_from_file_handle.repository_code_pointer_dict.keys()) == {
            'hello_world_repository'
        }
        assert isinstance(loaded_from_file_handle, PythonEnvRepositoryLocationHandle)

        loaded_from_module_handle = workspace.get_repository_location_handle('loaded_from_module')
        assert set(loaded_from_module_handle.repository_code_pointer_dict.keys()) == {
            'hello_world_repository'
        }
        assert isinstance(loaded_from_file_handle, PythonEnvRepositoryLocationHandle)

        named_loaded_from_file_handle = workspace.get_repository_location_handle(
            'named_loaded_from_file'
        )
        assert set(named_loaded_from_file_handle.repository_code_pointer_dict.keys()) == {
            'hello_world_repository_name'
        }
        assert isinstance(named_loaded_from_file_handle, PythonEnvRepositoryLocationHandle)

        named_loaded_from_module_handle = workspace.get_repository_location_handle(
            'named_loaded_from_module'
        )
        assert set(named_loaded_from_module_handle.repository_code_pointer_dict.keys()) == {
            'hello_world_repository_name'
        }
        assert isinstance(named_loaded_from_file_handle, PythonEnvRepositoryLocationHandle)

        named_loaded_from_module_attribute_handle = workspace.get_repository_location_handle(
            'named_loaded_from_module_attribute'
        )
        assert set(
            named_loaded_from_module_attribute_handle.repository_code_pointer_dict.keys()
        ) == {'hello_world_repository_name'}
        assert isinstance(
            named_loaded_from_module_attribute_handle, PythonEnvRepositoryLocationHandle
        )

        named_loaded_from_file_attribute_handle = workspace.get_repository_location_handle(
            'named_loaded_from_file_attribute'
        )
        assert set(named_loaded_from_file_attribute_handle.repository_code_pointer_dict.keys()) == {
            'hello_world_repository_name'
        }
        assert isinstance(
            named_loaded_from_file_attribute_handle, PythonEnvRepositoryLocationHandle
        )


def test_grpc_multi_location_workspace():
    with load_workspace_from_config(
        yaml.safe_load(_get_multi_location_workspace_yaml()),
        # fake out as if it were loaded by a yaml file in this directory
        file_relative_path(__file__, 'not_a_real.yaml'),
        UserProcessApi.GRPC,
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 6
        assert workspace.has_repository_location_handle('loaded_from_file')
        assert workspace.has_repository_location_handle('loaded_from_module')

        loaded_from_file_handle = workspace.get_repository_location_handle('loaded_from_file')
        assert isinstance(loaded_from_file_handle, ManagedGrpcPythonEnvRepositoryLocationHandle)

        assert loaded_from_file_handle.repository_names == {'hello_world_repository'}

        loaded_from_module_handle = workspace.get_repository_location_handle('loaded_from_module')
        assert isinstance(loaded_from_module_handle, ManagedGrpcPythonEnvRepositoryLocationHandle)

        assert loaded_from_module_handle.repository_names == {'hello_world_repository'}

        named_loaded_from_file_handle = workspace.get_repository_location_handle(
            'named_loaded_from_file'
        )
        assert named_loaded_from_file_handle.repository_names == {'hello_world_repository_name'}
        assert isinstance(
            named_loaded_from_file_handle, ManagedGrpcPythonEnvRepositoryLocationHandle
        )

        named_loaded_from_module_handle = workspace.get_repository_location_handle(
            'named_loaded_from_module'
        )
        assert named_loaded_from_module_handle.repository_names == {'hello_world_repository_name'}
        assert isinstance(
            named_loaded_from_file_handle, ManagedGrpcPythonEnvRepositoryLocationHandle
        )

        named_loaded_from_module_attribute_handle = workspace.get_repository_location_handle(
            'named_loaded_from_module_attribute'
        )
        assert named_loaded_from_module_attribute_handle.repository_names == {
            'hello_world_repository_name'
        }
        assert isinstance(
            named_loaded_from_module_attribute_handle, ManagedGrpcPythonEnvRepositoryLocationHandle
        )

        named_loaded_from_file_attribute_handle = workspace.get_repository_location_handle(
            'named_loaded_from_file_attribute'
        )
        assert named_loaded_from_file_attribute_handle.repository_names == {
            'hello_world_repository_name'
        }
        assert isinstance(
            named_loaded_from_file_attribute_handle, ManagedGrpcPythonEnvRepositoryLocationHandle
        )
