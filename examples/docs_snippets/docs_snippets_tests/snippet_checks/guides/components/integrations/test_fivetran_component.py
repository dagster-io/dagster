import shutil
import textwrap
from collections.abc import Iterator, Mapping
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Optional

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
    / "fivetran-component"
)


def _swap_to_mock_fivetran_component(path: Path) -> None:
    path.write_text(
        path.read_text().replace(
            "dagster_fivetran.FivetranAccountComponent",
            "my_project.defs.fivetran_ingest.test_utils.MockFivetranComponent",
        )
    )


def test_components_docs_fivetran_workspace(
    update_snippets: bool,
    update_screenshots: bool,
    get_selenium_driver,
) -> None:
    with ExitStack() as stack:
        context = stack.enter_context(
            isolated_snippet_generation_environment(
                should_update_snippets=update_snippets,
                snapshot_base_dir=SNIPPETS_DIR,
                global_snippet_replace_regexes=[
                    MASK_VENV,
                    MASK_USING_LOG_MESSAGE,
                    MASK_MY_PROJECT,
                ],
            )
        )
        stack.enter_context(
            environ({"FIVETRAN_API_KEY": "XX", "FIVETRAN_API_SECRET": "XX"})
        )
        # Scaffold code location
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project/src",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("--editable.*dagster-fivetran", "dagster-fivetran"),
                ("create-dagster", "uvx create-dagster"),
            ],
            ignore_output=True,
        )

        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-fivetran'}",
            snippet_path=f"{context.get_next_snip_number()}-add-fivetran.txt",
            print_cmd="uv add dagster-fivetran",
            ignore_output=True,
        )

        stack.enter_context(activate_venv("../.venv"))

        # scaffold fivetran component
        context.run_command_and_snippet_output(
            cmd='dg scaffold defs dagster_fivetran.FivetranAccountComponent fivetran_ingest \\\n  --account-id test_account --api-key "{{ env.FIVETRAN_API_KEY }}" --api-secret "{{ env.FIVETRAN_API_SECRET }}"',
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-fivetran-component.txt",
        )

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("my_project") / "defs" / "fivetran_ingest" / "defs.yaml",
            snippet_path=f"{context.get_next_snip_number()}-component.yaml",
        )

        # copy test_utils.py to my-project
        shutil.copy(
            Path(__file__).parent / "test_utils.py",
            Path("my_project") / "defs" / "fivetran_ingest" / "test_utils.py",
        )

        _swap_to_mock_fivetran_component(
            Path("my_project") / "defs" / "fivetran_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with connector selector
        context.create_file(
            Path("my_project") / "defs" / "fivetran_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_fivetran.FivetranAccountComponent

                attributes:
                  workspace:
                    account_id: test_account
                    api_key: "{{ env.FIVETRAN_API_KEY }}"
                    api_secret: "{{ env.FIVETRAN_API_SECRET }}"
                  connector_selector:
                    by_name:
                      - salesforce_warehouse_sync
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        _swap_to_mock_fivetran_component(
            Path("my_project") / "defs" / "fivetran_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with translation
        context.create_file(
            Path("my_project") / "defs" / "fivetran_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_fivetran.FivetranAccountComponent

                attributes:
                  workspace:
                    account_id: test_account
                    api_key: "{{ env.FIVETRAN_API_KEY }}"
                    api_secret: "{{ env.FIVETRAN_API_SECRET }}"
                  connector_selector:
                    by_name:
                      - salesforce_warehouse_sync
                  translation:
                    group_name: fivetran_data
                    description: "Loads data from Fivetran connector {{ props.name }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        _swap_to_mock_fivetran_component(
            Path("my_project") / "defs" / "fivetran_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )
