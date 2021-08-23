from dagster import DagsterInstance, execute_pipeline
from dagster.core.workspace.load import load_workspace_process_context_from_yaml_paths
from dagster.utils import file_relative_path
from docs_snippets_crag.concepts.repositories_workspaces.hello_world_repository import (
    hello_world_pipeline,
    hello_world_repository,
)


def test_pipelines():
    result = execute_pipeline(hello_world_pipeline)
    assert result.success


def test_hello_world_repository():
    assert hello_world_repository
    assert len(hello_world_repository.get_all_pipelines()) == 1


def test_workspace_yamls():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets_crag/concepts/repositories_workspaces/workspace.yaml",
            )
        ],
    ) as workspace_process_context:
        assert workspace_process_context.repository_locations_count == 1

    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets_crag/concepts/repositories_workspaces/workspace_working_directory.yaml",
            )
        ],
    ) as workspace_process_context:
        assert workspace_process_context.repository_locations_count == 1

    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets_crag/concepts/repositories_workspaces/workspace_one_repository.yaml",
            )
        ],
    ) as workspace_process_context:
        assert workspace_process_context.repository_locations_count == 1

    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets_crag/concepts/repositories_workspaces/workspace_python_package.yaml",
            )
        ],
    ) as workspace_process_context:
        assert workspace_process_context.repository_locations_count == 1

    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets_crag/concepts/repositories_workspaces/workspace_grpc.yaml",
            )
        ],
    ) as workspace_process_context:
        assert workspace_process_context.repository_locations_count == 1
