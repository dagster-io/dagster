import shutil
import textwrap
from collections.abc import Iterator, Mapping
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from dagster_dg_core.utils import activate_venv

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
)
from docs_snippets_tests.snippet_checks.utils import (
    compare_tree_output,
    isolated_snippet_generation_environment,
)

MASK_MY_PROJECT = (r" \/.*?\/my-project", " /.../my-project")
MASK_VENV = (r"Using.*\.venv.*", "")
MASK_USING_LOG_MESSAGE = (r"Using.*\n", "")

SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "components"
    / "integrations"
    / "airbyte-component"
)


def _swap_to_mock_airbyte_component(path: Path) -> None:
    path.write_text(
        path.read_text().replace(
            "dagster_airbyte.AirbyteWorkspaceComponent",
            "my_project.defs.airbyte_ingest.test_airbyte_utils.MockAirbyteComponent",
        )
    )


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

        stack.enter_context(activate_venv("../.venv"))
        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-airbyte'}",
            snippet_path=f"{context.get_next_snip_number()}-add-airbyte.txt",
            print_cmd="uv add dagster-airbyte",
            ignore_output=True,
        )

        # scaffold airbyte component
        context.run_command_and_snippet_output(
            cmd='dg scaffold defs dagster_airbyte.AirbyteWorkspaceComponent airbyte_ingest \\\n  --workspace-id test_workspace --client-id "{{ env.AIRBYTE_CLIENT_ID }}" --client-secret "{{ env.AIRBYTE_CLIENT_SECRET }}"',
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-airbyte-component.txt",
        )

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("my_project") / "defs" / "airbyte_ingest" / "defs.yaml",
            snippet_path=f"{context.get_next_snip_number()}-component.yaml",
        )

        # copy test_utils.py to my-project
        shutil.copy(
            Path(__file__).parent / "test_airbyte_utils.py",
            Path("my_project") / "defs" / "airbyte_ingest" / "test_airbyte_utils.py",
        )

        _swap_to_mock_airbyte_component(
            Path("my_project") / "defs" / "airbyte_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Skip OSS component defs as they demonstrate the different authentication methods which
        # are already tested in the integration tests and considering the tests here mock the
        # entire AirbyteWorkspace class in test_airbyte_utils.py with MockAirbyteWorkspace, it seems
        # pretty pointless to test these.
        context._snip_number += 3  # noqa: SLF001

        # Update component.yaml with connection selector
        context.create_file(
            Path("my_project") / "defs" / "airbyte_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_airbyte.AirbyteWorkspaceComponent

                attributes:
                  workspace:
                    workspace_id: test_workspace
                    client_id: "{{ env.AIRBYTE_CLIENT_ID }}"
                    client_secret: "{{ env.AIRBYTE_CLIENT_SECRET }}"
                  connection_selector:
                    by_name:
                      - salesforce_to_snowflake
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        _swap_to_mock_airbyte_component(
            Path("my_project") / "defs" / "airbyte_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with translation
        context.create_file(
            Path("my_project") / "defs" / "airbyte_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_airbyte.AirbyteWorkspaceComponent

                attributes:
                  workspace:
                    workspace_id: test_workspace
                    client_id: "{{ env.AIRBYTE_CLIENT_ID }}"
                    client_secret: "{{ env.AIRBYTE_CLIENT_SECRET }}"
                  connection_selector:
                    by_name:
                      - salesforce_to_snowflake
                  translation:
                    group_name: airbyte_data
                    description: "Loads data from Airbyte connection {{ props.connection_name }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        _swap_to_mock_airbyte_component(
            Path("my_project") / "defs" / "airbyte_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )
