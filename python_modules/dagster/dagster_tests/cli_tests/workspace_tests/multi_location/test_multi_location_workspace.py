import sys
from contextlib import ExitStack

import pytest
import yaml
from dagster._core.remote_representation import GrpcServerCodeLocation
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load import (
    load_workspace_process_context_from_yaml_paths,
    location_origins_from_config,
)
from dagster._utils import file_relative_path


@pytest.fixture
def instance():
    with instance_for_test() as instance:
        yield instance


def test_multi_location_workspace_foo(instance):
    with load_workspace_process_context_from_yaml_paths(
        instance,
        [file_relative_path(__file__, "multi_location.yaml")],
    ) as grpc_workspace:
        assert isinstance(grpc_workspace, WorkspaceProcessContext)
        assert grpc_workspace.code_locations_count == 3
        assert grpc_workspace.has_code_location("loaded_from_file")
        assert grpc_workspace.has_code_location("loaded_from_module")
        assert grpc_workspace.has_code_location("loaded_from_package")


def test_multi_file_extend_workspace(instance):
    with load_workspace_process_context_from_yaml_paths(
        instance,
        [
            file_relative_path(__file__, "multi_location.yaml"),
            file_relative_path(__file__, "extra_location.yaml"),
        ],
    ) as workspace:
        assert isinstance(workspace, WorkspaceProcessContext)
        assert workspace.code_locations_count == 4
        assert workspace.has_code_location("loaded_from_file")
        assert workspace.has_code_location("loaded_from_module")
        assert workspace.has_code_location("loaded_from_package")
        assert workspace.has_code_location("extra_location")


def test_multi_file_override_workspace(instance):
    with load_workspace_process_context_from_yaml_paths(
        instance,
        [
            file_relative_path(__file__, "multi_location.yaml"),
            file_relative_path(__file__, "override_location.yaml"),
        ],
    ) as workspace:
        assert isinstance(workspace, WorkspaceProcessContext)
        assert workspace.code_locations_count == 3
        assert workspace.has_code_location("loaded_from_file")
        assert workspace.has_code_location("loaded_from_module")
        assert workspace.has_code_location("loaded_from_package")

        loaded_from_file = workspace.create_request_context().get_code_location("loaded_from_file")

        # Ensure location `loaded_from_file` has been overridden
        remote_repos = loaded_from_file.get_repositories()
        assert len(remote_repos) == 1
        assert "extra_repository" in remote_repos


def test_multi_file_extend_and_override_workspace(instance):
    with load_workspace_process_context_from_yaml_paths(
        instance,
        [
            file_relative_path(__file__, "multi_location.yaml"),
            file_relative_path(__file__, "override_location.yaml"),
            file_relative_path(__file__, "extra_location.yaml"),
        ],
    ) as workspace:
        assert isinstance(workspace, WorkspaceProcessContext)
        assert workspace.code_locations_count == 4
        assert workspace.has_code_location("loaded_from_file")
        assert workspace.has_code_location("loaded_from_module")
        assert workspace.has_code_location("loaded_from_package")
        assert workspace.has_code_location("extra_location")

        loaded_from_file = workspace.create_request_context().get_code_location("loaded_from_file")

        # Ensure location `loaded_from_file` has been overridden
        remote_repos = loaded_from_file.get_repositories()
        assert len(remote_repos) == 1
        assert "extra_repository" in remote_repos


def _get_multi_location_workspace_yaml(executable):
    return f"""
load_from:
    - python_file:
        executable_path: {executable}
        relative_path: hello_world_repository.py
        location_name: loaded_from_file

    - python_module:
        executable_path: {executable}
        module_name: dagster.utils.test.hello_world_repository
        location_name: loaded_from_module

    - python_file:
        executable_path: {executable}
        relative_path: named_hello_world_repository.py
        location_name: named_loaded_from_file

    - python_module:
        executable_path: {executable}
        module_name: dagster.utils.test.named_hello_world_repository
        location_name: named_loaded_from_module

    - python_module:
        executable_path: {executable}
        module_name: dagster.utils.test.named_hello_world_repository
        attribute: named_hello_world_repository
        location_name: named_loaded_from_module_attribute

    - python_file:
        executable_path: {executable}
        relative_path: named_hello_world_repository.py
        attribute: named_hello_world_repository
        location_name: named_loaded_from_file_attribute

    """


@pytest.mark.parametrize(
    "config_source",
    [_get_multi_location_workspace_yaml],
)
def test_multi_location_origins(config_source):
    fake_executable = "/var/fake/executable"

    origins = location_origins_from_config(
        yaml.safe_load(config_source(fake_executable)),
        file_relative_path(__file__, "not_a_real.yaml"),
    )

    assert len(origins) == 6

    assert sorted(origins.keys()) == sorted(
        [
            "loaded_from_file",
            "loaded_from_module",
            "named_loaded_from_file",
            "named_loaded_from_module",
            "named_loaded_from_module_attribute",
            "named_loaded_from_file_attribute",
        ]
    )

    assert all(
        [
            origin.loadable_target_origin.executable_path == fake_executable
            for origin in origins.values()
        ]
    )

    assert origins["loaded_from_file"].loadable_target_origin.python_file == file_relative_path(
        __file__, "hello_world_repository.py"
    )
    assert (
        origins["loaded_from_module"].loadable_target_origin.module_name
        == "dagster.utils.test.hello_world_repository"
    )

    assert (
        origins["named_loaded_from_file_attribute"].loadable_target_origin.attribute
        == "named_hello_world_repository"
    )
    assert (
        origins["named_loaded_from_module_attribute"].loadable_target_origin.attribute
        == "named_hello_world_repository"
    )


@pytest.mark.parametrize("config_source", [_get_multi_location_workspace_yaml])
def test_grpc_multi_location_workspace(config_source):
    origins = location_origins_from_config(
        yaml.safe_load(config_source(sys.executable)),
        # fake out as if it were loaded by a yaml file in this directory
        file_relative_path(__file__, "not_a_real.yaml"),
    )
    with ExitStack() as stack:
        instance = stack.enter_context(instance_for_test())
        code_locations = {
            name: stack.enter_context(origin.create_single_location(instance))  # pyright: ignore[reportAttributeAccessIssue]
            for name, origin in origins.items()
        }

        assert len(code_locations) == 6
        assert "loaded_from_file" in code_locations
        assert "loaded_from_module" in code_locations

        loaded_from_file_location = code_locations.get("loaded_from_file")
        assert isinstance(loaded_from_file_location, GrpcServerCodeLocation)
        assert loaded_from_file_location.repository_names == {"hello_world_repository"}

        loaded_from_module_location = code_locations.get("loaded_from_module")
        assert isinstance(loaded_from_module_location, GrpcServerCodeLocation)

        assert loaded_from_module_location.repository_names == {"hello_world_repository"}

        named_loaded_from_file_location = code_locations.get("named_loaded_from_file")
        assert named_loaded_from_file_location.repository_names == {"hello_world_repository_name"}  # pyright: ignore[reportOptionalMemberAccess]
        assert isinstance(named_loaded_from_file_location, GrpcServerCodeLocation)

        named_loaded_from_module_location = code_locations.get("named_loaded_from_module")
        assert named_loaded_from_module_location.repository_names == {"hello_world_repository_name"}  # pyright: ignore[reportOptionalMemberAccess]
        assert isinstance(named_loaded_from_module_location, GrpcServerCodeLocation)

        named_loaded_from_module_attribute_location = code_locations.get(
            "named_loaded_from_module_attribute"
        )
        assert named_loaded_from_module_attribute_location.repository_names == {  # pyright: ignore[reportOptionalMemberAccess]
            "hello_world_repository_name"
        }
        assert isinstance(named_loaded_from_module_attribute_location, GrpcServerCodeLocation)

        named_loaded_from_file_attribute_location = code_locations.get(
            "named_loaded_from_file_attribute"
        )
        assert named_loaded_from_file_attribute_location.repository_names == {  # pyright: ignore[reportOptionalMemberAccess]
            "hello_world_repository_name"
        }
        assert isinstance(named_loaded_from_file_attribute_location, GrpcServerCodeLocation)
