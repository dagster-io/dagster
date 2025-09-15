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
    / "sling-component"
)


def test_components_docs_sling_workspace(
    update_snippets: bool,
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
        ExitStack() as stack,
    ):
        # Scaffold code location
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project/src",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("--editable.*dagster-sling", "dagster-sling"),
            ],
            ignore_output=True,
        )

        stack.enter_context(activate_venv("../.venv"))
        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-sling'}",
            snippet_path=f"{context.get_next_snip_number()}-add-sling.txt",
            print_cmd="uv add dagster-sling duckdb",
            ignore_output=True,
        )

        # scaffold sling component
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster_sling.SlingReplicationCollectionComponent sling_ingest",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-sling-component.txt",
            snippet_replace_regex=[
                (r"Downloading sling binary.*\n", ""),
            ],
        )

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("my_project") / "defs" / "sling_ingest" / "defs.yaml",
            snippet_path=f"{context.get_next_snip_number()}-component.yaml",
        )

        context.check_file(
            Path("my_project") / "defs" / "sling_ingest" / "replication.yaml",
            snippet_path=f"{context.get_next_snip_number()}-replication.yaml",
        )

        # Download sample data files
        context.run_command_and_snippet_output(
            cmd=textwrap.dedent("""
                curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv &&
                curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv &&
                curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv
            """).strip(),
            snippet_path=f"{context.get_next_snip_number()}-curl.txt",
            ignore_output=True,
        )

        # Create replication.yaml with sample data configuration
        context.create_file(
            Path("my_project") / "defs" / "sling_ingest" / "replication.yaml",
            contents=textwrap.dedent(
                """\
                source: LOCAL
                target: DUCKDB

                defaults:
                  mode: full-refresh
                  object: "{stream_table}"

                streams:
                  file://raw_customers.csv:
                    object: "main.raw_customers"
                  file://raw_orders.csv:
                    object: "main.raw_orders"
                  file://raw_payments.csv:
                    object: "main.raw_payments"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-replication.yaml",
        )

        # Update component.yaml with connection selector
        context.create_file(
            Path("my_project") / "defs" / "sling_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_sling.SlingReplicationCollectionComponent

                attributes:
                  connections:
                    DUCKDB:
                      type: duckdb
                      instance: /tmp/my_project.duckdb
                  replications:
                    - path: ./replication.yaml
                    """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with translation
        context.create_file(
            Path("my_project") / "defs" / "sling_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_sling.SlingReplicationCollectionComponent

                attributes:
                  connections:
                    DUCKDB:
                      type: duckdb
                      instance: /tmp/my_project.duckdb
                  replications:
                    - path: ./replication.yaml
                      translation:
                        group_name: sling_data
                        description: "Loads data from Sling replication {{ stream_definition.name }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )
