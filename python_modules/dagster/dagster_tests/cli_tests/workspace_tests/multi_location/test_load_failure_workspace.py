from dagster.cli.workspace import Workspace
from dagster.cli.workspace.load import load_workspace_from_yaml_paths
from dagster.core.host_representation.handle import UserProcessApi
from dagster.utils import file_relative_path


def test_multi_location_error():
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "multi_location_with_error.yaml")], UserProcessApi.CLI,
    ) as cli_workspace:
        assert isinstance(cli_workspace, Workspace)
        assert len(cli_workspace.repository_location_handles) == 1

        assert len(cli_workspace.repository_location_errors) == 1

        assert cli_workspace.has_repository_location_handle("working_location")
        assert not cli_workspace.has_repository_location_handle("broken_location")

        assert not cli_workspace.has_repository_location_error("working_location")
        assert cli_workspace.has_repository_location_error("broken_location")

        assert (
            "No module named"
            in cli_workspace.get_repository_location_error("broken_location").message
        )


# A workspace still loads even if there's an error loading all of its locations
def test_workspace_with_only_error():
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "workspace_with_only_error.yaml")], UserProcessApi.CLI,
    ) as cli_workspace:
        assert isinstance(cli_workspace, Workspace)
        assert len(cli_workspace.repository_location_handles) == 0

        assert len(cli_workspace.repository_location_errors) == 1

        assert not cli_workspace.has_repository_location_handle("broken_location")
        assert cli_workspace.has_repository_location_error("broken_location")

        assert (
            "No module named"
            in cli_workspace.get_repository_location_error("broken_location").message
        )
