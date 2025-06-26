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
            cmd="dg scaffold defs dagster_snowflake.SnowflakeTemplatedSqlComponent daily_revenue",
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

        # Create resources.py file (real resource for user-facing snapshot)
        context.create_file(
            Path("my_project") / "defs" / "resources.py",
            contents=textwrap.dedent(
                """\
                from dagster_snowflake import SnowflakeResource

                import dagster as dg

                defs = dg.Definitions(
                    resources={
                        "snowflake": SnowflakeResource(
                            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
                            user=dg.EnvVar("SNOWFLAKE_USER"),
                            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
                            database=dg.EnvVar("SNOWFLAKE_DATABASE"),
                            schema=dg.EnvVar("SNOWFLAKE_SCHEMA"),
                        )
                    }
                )
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-resources.py",
        )

        # Now populate the defs.yaml file with the correct content
        context.create_file(
            Path("my_project") / "defs" / "daily_revenue" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_snowflake.SnowflakeTemplatedSqlComponent

                attributes:
                  sql_template: |
                    SELECT
                      DATE_TRUNC('day', {{ date_column }}) as date,
                      SUM({{ amount_column }}) as daily_revenue
                    FROM {{ table_name }}
                    WHERE {{ date_column }} >= '{{ start_date }}'
                    GROUP BY DATE_TRUNC('day', {{ date_column }})
                    ORDER BY date
                  assets:
                    - key: ANALYTICS/DAILY_REVENUE
                      group_name: analytics
                      kinds: [snowflake]
                  sql_template_vars:
                    table_name: SALES_TRANSACTIONS
                    date_column: TRANSACTION_DATE
                    amount_column: SALE_AMOUNT
                    start_date: "2024-01-01"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        # copy test_snowflake_utils.py to my-project
        shutil.copy(
            Path(__file__).parent / "test_snowflake_utils.py",
            Path("my_project") / "defs" / "daily_revenue" / "test_snowflake_utils.py",
        )

        # Before running the asset (before the first dg list defs), swap in the mock resource
        context.create_file(
            Path("my_project") / "defs" / "resources.py",
            contents=textwrap.dedent(
                """\
                import dagster as dg
                from .daily_revenue.test_snowflake_utils import MockSnowflakeResource

                defs = dg.Definitions(
                    resources={
                        "snowflake": MockSnowflakeResource(
                            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
                            user=dg.EnvVar("SNOWFLAKE_USER"),
                            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
                            database=dg.EnvVar("SNOWFLAKE_DATABASE"),
                            schema=dg.EnvVar("SNOWFLAKE_SCHEMA"),
                        )
                    }
                )
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
