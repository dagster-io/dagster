import pytest

from dagster import DagsterInstance
from dagster._core.instance_for_test import instance_for_test
from dagster._core.workspace.load import load_workspace_process_context_from_yaml_paths
from dagster._utils import file_relative_path
from docs_snippets.concepts.repositories_workspaces.hello_world_repository import (
    hello_world_job,
    hello_world_repository,
)


def test_jobs():
    result = hello_world_job.execute_in_process()
    assert result.success


def test_hello_world_repository():
    assert hello_world_repository
    assert len(hello_world_repository.get_all_jobs()) == 1


@pytest.fixture
def instance():
    with instance_for_test() as my_instance:
        yield my_instance


def test_workspace_yamls(instance):
    with load_workspace_process_context_from_yaml_paths(
        instance,
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets/concepts/repositories_workspaces/workspace.yaml",
            )
        ],
    ) as workspace_process_context:
        assert workspace_process_context.code_locations_count == 1

    with load_workspace_process_context_from_yaml_paths(
        instance,
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets/concepts/repositories_workspaces/workspace_working_directory.yaml",
            )
        ],
    ) as workspace_process_context:
        assert workspace_process_context.code_locations_count == 1

    with load_workspace_process_context_from_yaml_paths(
        instance,
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets/concepts/repositories_workspaces/workspace_one_repository.yaml",
            )
        ],
    ) as workspace_process_context:
        assert workspace_process_context.code_locations_count == 1

    with load_workspace_process_context_from_yaml_paths(
        instance,
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets/concepts/repositories_workspaces/workspace_python_module.yaml",
            )
        ],
    ) as workspace_process_context:
        assert workspace_process_context.code_locations_count == 1

    with load_workspace_process_context_from_yaml_paths(
        instance,
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets/concepts/repositories_workspaces/workspace_grpc.yaml",
            )
        ],
    ) as workspace_process_context:
        assert workspace_process_context.code_locations_count == 1
