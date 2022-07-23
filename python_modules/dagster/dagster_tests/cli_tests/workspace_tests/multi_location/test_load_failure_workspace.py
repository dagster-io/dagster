from dagster import DagsterInstance
from dagster._utils import file_relative_path
from dagster.core.workspace.context import WorkspaceProcessContext
from dagster.core.workspace.load import load_workspace_process_context_from_yaml_paths


def test_multi_location_error():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [file_relative_path(__file__, "multi_location_with_error.yaml")],
    ) as cli_workspace:
        assert isinstance(cli_workspace, WorkspaceProcessContext)
        assert cli_workspace.repository_locations_count == 2

        assert cli_workspace.has_repository_location("working_location")
        assert not cli_workspace.has_repository_location("broken_location")
        assert not cli_workspace.has_repository_location("completely_unknown_location")

        request_context = cli_workspace.create_request_context()

        assert len(request_context.repository_location_errors()) == 1
        assert not request_context.has_repository_location_error("working_location")
        assert request_context.has_repository_location_error("broken_location")
        assert not request_context.has_repository_location("completely_unknown_location")

        assert (
            "No module named"
            in request_context.get_repository_location_error("broken_location").message
        )


# A workspace still loads even if there's an error loading all of its locations
def test_workspace_with_only_error():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [file_relative_path(__file__, "workspace_with_only_error.yaml")],
    ) as cli_workspace:
        assert isinstance(cli_workspace, WorkspaceProcessContext)
        assert cli_workspace.repository_locations_count == 1
        assert not cli_workspace.has_repository_location("broken_location")

        request_context = cli_workspace.create_request_context()
        assert len(request_context.repository_location_errors()) == 1

        assert request_context.has_repository_location_error("broken_location")

        assert (
            "No module named"
            in request_context.get_repository_location_error("broken_location").message
        )
