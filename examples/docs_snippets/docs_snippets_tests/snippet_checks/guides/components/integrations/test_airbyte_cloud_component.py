from collections.abc import Sequence
from functools import cached_property
from typing import Optional

from dagster_airbyte import AirbyteCloudWorkspace
from dagster_airbyte.components.workspace_component.component import (
    AirbyteCloudWorkspaceComponent,
)
from dagster_airbyte.translator import (
    AirbyteConnection,
    AirbyteDestination,
    AirbyteStream,
    AirbyteWorkspaceData,
)

from dagster._utils.cached_method import cached_method


class MockAirbyteWorkspace(AirbyteCloudWorkspace):
    @cached_method
    def fetch_airbyte_workspace_data(
        self,
    ) -> AirbyteWorkspaceData:
        """Retrieves all Airbyte content from the workspace and returns it as a AirbyteWorkspaceData object.

        Returns:
            AirbyteWorkspaceData: A snapshot of the Airbyte workspace's content.
        """
        # connections_by_id = {}
        # destinations_by_id = {}

def test_components_docs_airbyte_workspace(
    update_snippets: bool,
    update_screenshots: bool,
    get_selenium_driver,
) -> None:
    with (
        isolated_snippet_generation_environment(
            should_update_snippets=update_snippets,
            snapshot_base_dir=SNIPPETS_DIR,
            global_snippet_replace_regexes=[
                MASK_VENV,
                MASK_USING_LOG_MESSAGE,
                MASK_MY_PROJECT,
            ],
        ) as context,
        environ(
            {
                "AIRBYTE_CLIENT_ID": "XX",
                "AIRBYTE_CLIENT_SECRET": "XX",
                "AIRBYTE_WORKSPACE_ID": "XX",
            }
        ),
        ExitStack() as stack,
    ):
        # Scaffold code location
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project/src",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("--editable.*dagster-airbyte", "dagster-airbyte"),
            ],
            ignore_output=True,
        )


class MockAirbyteComponent(AirbyteCloudWorkspaceComponent):
    @cached_property
    def workspace_resource(self) -> MockAirbyteWorkspace:
        return MockAirbyteWorkspace(**self.workspace.model_dump())