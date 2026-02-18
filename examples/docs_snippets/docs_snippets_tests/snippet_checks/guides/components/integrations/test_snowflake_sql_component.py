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
MASK_PKG_RESOURCES = (r"\n.*import pkg_resources\n", "")

SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "components"
    / "integrations"
    / "snowflake-sql-component"
)


def test_components_docs_snowflake_sql(
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
                MASK_PKG_RESOURCES,
            ],
        ) as context,
        environ(
            {
                "SNOWFLAKE_ACCOUNT": "test_account",
                "SNOWFLAKE_USER": "test_user",
                "SNOWFLAKE_PASSWORD": "test_password",
                "SNOWFLAKE_DATABASE": "TESTDB",
                "SNOWFLAKE_SCHEMA": "TESTSCHEMA",
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
                ("--editable.*dagster-snowflake", "dagster-snowflake"),
            ],
            ignore_output=True,
        )

        stack.enter_context(activate_venv("../.venv"))
        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-snowflake'}",
            snippet_path=f"{context.get_next_snip_number()}-add-snowflake.txt",
            print_cmd="uv add dagster-snowflake",
            ignore_output=True,
        )

        # scaffold snowflake sql component (no args)
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster.TemplatedSqlComponent daily_revenue",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-snowflake-component.txt",
        )

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("my_project") / "defs" / "daily_revenue" / "defs.yaml",
            snippet_path=f"{context.get_next_snip_number()}-component.yaml",
        )

        # Create a connection component for Snowflake
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster_snowflake.SnowflakeConnectionComponent snowflake_connection",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-connection-component.txt",
        )

        # Update the connection component with actual connection details
        context.create_file(
            Path("my_project") / "defs" / "snowflake_connection" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_snowflake.SnowflakeConnectionComponent

                attributes:
                  account: "{{ env.SNOWFLAKE_ACCOUNT }}"
                  user: "{{ env.SNOWFLAKE_USER }}"
                  password: "{{ env.SNOWFLAKE_PASSWORD }}"
                  database: "{{ env.SNOWFLAKE_DATABASE }}"
                  schema: "{{ env.SNOWFLAKE_SCHEMA }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-connection-component.yaml",
        )

        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        # Now populate the defs.yaml file with the correct content using external connection
        context.create_file(
            Path("my_project") / "defs" / "daily_revenue" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster.TemplatedSqlComponent

                attributes:
                  sql_template: |
                    SELECT
                      DATE_TRUNC('day', {{ date_column }}) as date,
                      SUM({{ amount_column }}) as daily_revenue
                    FROM {{ table_name }}
                    WHERE {{ date_column }} >= '{{ start_date }}'
                    GROUP BY DATE_TRUNC('day', {{ date_column }})
                    ORDER BY date

                  sql_template_vars:
                    table_name: SALES_TRANSACTIONS
                    date_column: TRANSACTION_DATE
                    amount_column: SALE_AMOUNT
                    start_date: "2024-01-01"

                  connection: "{{ load_component_at_path('snowflake_connection') }}"

                  assets:
                    - key: ANALYTICS/DAILY_REVENUE
                      group_name: analytics
                      kinds: [snowflake]
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        # Before running the asset (before the first dg list defs), swap in the mock connection
        shutil.copy(
            Path(__file__).parent / "test_snowflake_utils.py",
            Path("my_project")
            / "defs"
            / "snowflake_connection"
            / "test_snowflake_utils.py",
        )
        context.create_file(
            Path("my_project") / "defs" / "snowflake_connection" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: my_project.defs.snowflake_connection.test_snowflake_utils.MockSqlConnectionComponent

                attributes:
                  account: "{{ env.SNOWFLAKE_ACCOUNT }}"
                  user: "{{ env.SNOWFLAKE_USER }}"
                  password: "{{ env.SNOWFLAKE_PASSWORD }}"
                  database: "{{ env.SNOWFLAKE_DATABASE }}"
                  schema: "{{ env.SNOWFLAKE_SCHEMA }}"
                """
            ),
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Launch the asset (materialize) after the final dg list defs
        context.run_command_and_snippet_output(
            cmd="dg launch --assets '*'",
            snippet_path=f"{context.get_next_snip_number()}-launch.txt",
            ignore_output=True,
        )

        # Create an external SQL file
        context.create_file(
            Path("my_project") / "defs" / "daily_revenue" / "daily_revenue.sql",
            contents=textwrap.dedent(
                """\
                SELECT
                  DATE_TRUNC('day', {{ date_column }}) as date,
                  SUM({{ amount_column }}) as daily_revenue
                FROM {{ table_name }}
                WHERE {{ date_column }} >= '{{ start_date }}'
                GROUP BY DATE_TRUNC('day', {{ date_column }})
                ORDER BY date
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-sql-file.sql",
        )

        # Update the component to reference the external SQL file and connection
        context.create_file(
            Path("my_project") / "defs" / "daily_revenue" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster.TemplatedSqlComponent

                attributes:
                  sql_template:
                    path: daily_revenue.sql

                  sql_template_vars:
                    table_name: SALES_TRANSACTIONS
                    date_column: TRANSACTION_DATE
                    amount_column: SALE_AMOUNT
                    start_date: "2024-01-01"

                  connection: "{{ load_component_at_path('snowflake_connection') }}"

                  assets:
                    - key: ANALYTICS/DAILY_REVENUE
                      group_name: analytics
                      kinds: [snowflake]
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-file-based-component.yaml",
        )

        # Show the updated project structure
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree-with-sql.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Launch the asset (materialize) after the final dg list defs
        context.run_command_and_snippet_output(
            cmd="dg launch --assets '*'",
            snippet_path=f"{context.get_next_snip_number()}-launch.txt",
            ignore_output=True,
        )
