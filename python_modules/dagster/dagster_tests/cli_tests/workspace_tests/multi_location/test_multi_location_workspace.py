import sys

import yaml
from dagster.cli.workspace import Workspace
from dagster.cli.workspace.load import load_workspace_from_config, load_workspace_from_yaml_paths
from dagster.core.host_representation import (
    ManagedGrpcPythonEnvRepositoryLocationHandle,
    RepositoryLocation,
)
from dagster.serdes import serialize_dagster_namedtuple
from dagster.utils import file_relative_path


def _get_single_code_pointer(workspace, location_name):
    return next(
        iter(
            workspace.get_repository_location_handle(
                location_name
            ).repository_code_pointer_dict.values()
        )
    )


def test_multi_location_workspace_foo():
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "multi_location.yaml")],
    ) as cli_workspace:
        assert isinstance(cli_workspace, Workspace)
        assert len(cli_workspace.repository_location_handles) == 3
        assert cli_workspace.has_repository_location_handle("loaded_from_file")
        assert cli_workspace.has_repository_location_handle("loaded_from_module")
        assert cli_workspace.has_repository_location_handle("loaded_from_package")

        with load_workspace_from_yaml_paths(
            [file_relative_path(__file__, "multi_location.yaml")],
        ) as grpc_workspace:
            assert isinstance(grpc_workspace, Workspace)
            assert len(grpc_workspace.repository_location_handles) == 3
            assert grpc_workspace.has_repository_location_handle("loaded_from_file")
            assert grpc_workspace.has_repository_location_handle("loaded_from_module")
            assert grpc_workspace.has_repository_location_handle("loaded_from_package")

            assert serialize_dagster_namedtuple(
                _get_single_code_pointer(cli_workspace, "loaded_from_file")
            ) == serialize_dagster_namedtuple(
                _get_single_code_pointer(grpc_workspace, "loaded_from_file")
            )

            assert serialize_dagster_namedtuple(
                _get_single_code_pointer(cli_workspace, "loaded_from_module")
            ) == serialize_dagster_namedtuple(
                _get_single_code_pointer(grpc_workspace, "loaded_from_module")
            )

            assert serialize_dagster_namedtuple(
                _get_single_code_pointer(cli_workspace, "loaded_from_package")
            ) == serialize_dagster_namedtuple(
                _get_single_code_pointer(grpc_workspace, "loaded_from_package")
            )


def test_multi_file_extend_workspace():
    with load_workspace_from_yaml_paths(
        [
            file_relative_path(__file__, "multi_location.yaml"),
            file_relative_path(__file__, "extra_location.yaml"),
        ],
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 4
        assert workspace.has_repository_location_handle("loaded_from_file")
        assert workspace.has_repository_location_handle("loaded_from_module")
        assert workspace.has_repository_location_handle("loaded_from_package")
        assert workspace.has_repository_location_handle("extra_location")


def test_multi_file_override_workspace():
    with load_workspace_from_yaml_paths(
        [
            file_relative_path(__file__, "multi_location.yaml"),
            file_relative_path(__file__, "override_location.yaml"),
        ],
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 3
        assert workspace.has_repository_location_handle("loaded_from_file")
        assert workspace.has_repository_location_handle("loaded_from_module")
        assert workspace.has_repository_location_handle("loaded_from_package")

        loaded_from_file = RepositoryLocation.from_handle(
            workspace.get_repository_location_handle("loaded_from_file")
        )

        # Ensure location `loaded_from_file` has been overridden
        external_repositories = loaded_from_file.get_repositories()
        assert len(external_repositories) == 1
        assert "extra_repository" in external_repositories


def test_multi_file_extend_and_override_workspace():
    with load_workspace_from_yaml_paths(
        [
            file_relative_path(__file__, "multi_location.yaml"),
            file_relative_path(__file__, "override_location.yaml"),
            file_relative_path(__file__, "extra_location.yaml"),
        ],
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 4
        assert workspace.has_repository_location_handle("loaded_from_file")
        assert workspace.has_repository_location_handle("loaded_from_module")
        assert workspace.has_repository_location_handle("loaded_from_package")
        assert workspace.has_repository_location_handle("extra_location")

        loaded_from_file = RepositoryLocation.from_handle(
            workspace.get_repository_location_handle("loaded_from_file")
        )

        # Ensure location `loaded_from_file` has been overridden
        external_repositories = loaded_from_file.get_repositories()
        assert len(external_repositories) == 1
        assert "extra_repository" in external_repositories


def _get_multi_location_workspace_yaml():
    return """
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

    """.format(
        executable=sys.executable
    )


def test_grpc_multi_location_workspace():
    with load_workspace_from_config(
        yaml.safe_load(_get_multi_location_workspace_yaml()),
        # fake out as if it were loaded by a yaml file in this directory
        file_relative_path(__file__, "not_a_real.yaml"),
    ) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 6
        assert workspace.has_repository_location_handle("loaded_from_file")
        assert workspace.has_repository_location_handle("loaded_from_module")

        loaded_from_file_handle = workspace.get_repository_location_handle("loaded_from_file")
        assert isinstance(loaded_from_file_handle, ManagedGrpcPythonEnvRepositoryLocationHandle)

        assert loaded_from_file_handle.repository_names == {"hello_world_repository"}

        loaded_from_module_handle = workspace.get_repository_location_handle("loaded_from_module")
        assert isinstance(loaded_from_module_handle, ManagedGrpcPythonEnvRepositoryLocationHandle)

        assert loaded_from_module_handle.repository_names == {"hello_world_repository"}

        named_loaded_from_file_handle = workspace.get_repository_location_handle(
            "named_loaded_from_file"
        )
        assert named_loaded_from_file_handle.repository_names == {"hello_world_repository_name"}
        assert isinstance(
            named_loaded_from_file_handle, ManagedGrpcPythonEnvRepositoryLocationHandle
        )

        named_loaded_from_module_handle = workspace.get_repository_location_handle(
            "named_loaded_from_module"
        )
        assert named_loaded_from_module_handle.repository_names == {"hello_world_repository_name"}
        assert isinstance(
            named_loaded_from_file_handle, ManagedGrpcPythonEnvRepositoryLocationHandle
        )

        named_loaded_from_module_attribute_handle = workspace.get_repository_location_handle(
            "named_loaded_from_module_attribute"
        )
        assert named_loaded_from_module_attribute_handle.repository_names == {
            "hello_world_repository_name"
        }
        assert isinstance(
            named_loaded_from_module_attribute_handle, ManagedGrpcPythonEnvRepositoryLocationHandle
        )

        named_loaded_from_file_attribute_handle = workspace.get_repository_location_handle(
            "named_loaded_from_file_attribute"
        )
        assert named_loaded_from_file_attribute_handle.repository_names == {
            "hello_world_repository_name"
        }
        assert isinstance(
            named_loaded_from_file_attribute_handle, ManagedGrpcPythonEnvRepositoryLocationHandle
        )
