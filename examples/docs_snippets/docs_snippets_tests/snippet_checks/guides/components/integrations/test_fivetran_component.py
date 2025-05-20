import textwrap
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, Optional

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    isolated_snippet_generation_environment,
)
from docs_snippets_tests.snippet_checks.utils import (
    check_file,
    compare_tree_output,
    create_file,
    run_command_and_snippet_output,
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


def test_components_docs_fivetran_workspace(
    update_snippets: bool,
    update_screenshots: bool,
    get_selenium_driver,
) -> None:
    with (
        isolated_snippet_generation_environment() as get_next_snip_number,
        environ({"FIVETRAN_API_KEY": "XX", "FIVETRAN_API_SECRET": "XX"}),
    ):
        # Scaffold code location
        run_command_and_snippet_output(
            cmd="dg scaffold project my-project --python-environment uv_managed --use-editable-dagster && cd my-project/src",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--python-environment uv_managed --use-editable-dagster ", ""),
                ("--editable.*dagster-fivetran", "dagster-fivetran"),
            ],
            update_snippets=update_snippets,
            ignore_output=True,
        )

        run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-fivetran'}",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-add-fivetran.txt",
            update_snippets=update_snippets,
            print_cmd="uv add dagster-fivetran",
            ignore_output=True,
        )

        # scaffold fivetran component
        run_command_and_snippet_output(
            cmd="dg scaffold dagster_fivetran.FivetranWorkspaceComponent fivetran_ingest \\\n  --account-id test_account --api-key \"env('FIVETRAN_API_KEY')\" --api-secret \"env('FIVETRAN_API_SECRET')\"",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffold-fivetran-component.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_PROJECT],
        )

        # Tree the project
        run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        check_file(
            Path("my_project") / "defs" / "fivetran_ingest" / "component.yaml",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-component.yaml",
            update_snippets=update_snippets,
        )

        # List defs
        run_command_and_snippet_output(
            cmd="dg check yaml",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_VENV, MASK_USING_LOG_MESSAGE],
        )

        # Update component.yaml with connector selector
        create_file(
            Path("my_project") / "defs" / "fivetran_ingest" / "component.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_fivetran.FivetranWorkspaceComponent

                attributes:
                  workspace:
                    account_id: test_account
                    api_key: "env('FIVETRAN_API_KEY')"
                    api_secret: "env('FIVETRAN_API_SECRET')"
                  connector_selector:
                    by_name:
                      - test_connector
                      - another_connector
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-customized-component.yaml",
        )

        # List defs again
        run_command_and_snippet_output(
            cmd="dg check yaml",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_VENV, MASK_USING_LOG_MESSAGE],
        )

        # Update component.yaml with translation
        create_file(
            Path("my_project") / "defs" / "fivetran_ingest" / "component.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_fivetran.FivetranWorkspaceComponent

                attributes:
                  workspace:
                    account_id: test_account
                    api_key: "env('FIVETRAN_API_KEY')"
                    api_secret: "env('FIVETRAN_API_SECRET')"
                  connector_selector:
                    by_name:
                      - test_connector
                  translation:
                    group_name: fivetran_data
                    description: "Loads data from Fivetran connector test_connector"
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-customized-component.yaml",
        )

        # List defs one more time
        run_command_and_snippet_output(
            cmd="dg check yaml",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_VENV, MASK_USING_LOG_MESSAGE],
        )
