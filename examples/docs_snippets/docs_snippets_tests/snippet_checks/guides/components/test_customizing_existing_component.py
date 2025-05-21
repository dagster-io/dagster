import textwrap
from pathlib import Path

import pytest

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    format_multiline,
    isolated_snippet_generation_environment,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    check_file,
    compare_tree_output,
    create_file,
    run_command_and_snippet_output,
    screenshot_page,
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
    / "customizing-existing-component"
)

CUSTOM_SLING_COMPONENT_BODY = '''\
from dagster_sling import SlingReplicationCollectionComponent


class CustomSlingReplicationComponent(SlingReplicationCollectionComponent):
    """Customized Sling component."""
'''


@pytest.mark.parametrize("component_type", ["local", "global"])
def test_components_docs_adding_attributes_to_assets(
    update_snippets: bool, update_screenshots: bool, get_selenium_driver, component_type
) -> None:
    with isolated_snippet_generation_environment() as get_next_snip_number:
        # Scaffold code location, add some assets
        run_command_and_snippet_output(
            cmd=textwrap.dedent(
                f"""\
                dg scaffold project my-project --python-environment uv_managed --use-editable-dagster \\
                    && cd my-project/src \\
                    && uv add --editable {EDITABLE_DIR / "dagster-sling"} \\
                    && dg scaffold dagster_sling.SlingReplicationCollectionComponent my_sling_sync\
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--python-environment uv_managed --use-editable-dagster ", ""),
                ("--editable.*dagster-sling", "dagster-sling"),
            ],
            update_snippets=update_snippets,
            ignore_output=True,
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")

        # Tree the project
        run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        if component_type == "local":
            component_py_path = (
                Path("my_project") / "defs" / "my_sling_sync" / "component.py"
            )
            create_file(
                component_py_path,
                contents=CUSTOM_SLING_COMPONENT_BODY,
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{get_next_snip_number()}-component.py",
            )
            run_command_and_snippet_output(
                cmd="tree my_project",
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{get_next_snip_number()}-tree.txt",
                update_snippets=update_snippets,
                custom_comparison_fn=compare_tree_output,
            )
            create_file(
                Path("my_project") / "defs" / "my_sling_sync" / "component.yaml",
                contents=(
                    Path("my_project") / "defs" / "my_sling_sync" / "component.yaml"
                )
                .read_text()
                .replace(
                    "dagster_sling.SlingReplicationCollectionComponent",
                    "my_project.defs.my_sling_sync.component.CustomSlingReplicationComponent",
                ),
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{get_next_snip_number()}-component.yaml",
            )
            get_next_snip_number()
        elif component_type == "global":
            component_py_path = (
                Path("my_project")
                / "components"
                / "custom_sling_replication_component.py"
            )
            run_command_and_snippet_output(
                cmd="dg scaffold component-type CustomSlingReplicationComponent",
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{get_next_snip_number()}-scaffold-component-type.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[MASK_MY_PROJECT],
            )
            create_file(
                component_py_path,
                contents=CUSTOM_SLING_COMPONENT_BODY,
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{get_next_snip_number()}-component.py",
            )
            run_command_and_snippet_output(
                cmd="tree my_project",
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{get_next_snip_number()}-tree.txt",
                update_snippets=update_snippets,
                custom_comparison_fn=compare_tree_output,
            )
            create_file(
                Path("my_project") / "defs" / "my_sling_sync" / "component.yaml",
                contents=(
                    Path("my_project") / "defs" / "my_sling_sync" / "component.yaml"
                )
                .read_text()
                .replace(
                    "dagster_sling.SlingReplicationCollectionComponent",
                    "my_project.components.CustomSlingReplicationComponent",
                ),
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{get_next_snip_number()}-component.yaml",
            )

        _run_command("dg check yaml")

        # Set up DuckDB to run, verify everything works ok
        _run_command(
            cmd=textwrap.dedent("""
                curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv &&
                curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv &&
                curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv
            """).strip(),
        )
        create_file(
            file_path=Path("my_project")
            / "defs"
            / "my_sling_sync"
            / "replication.yaml",
            contents=textwrap.dedent(
                """
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
            """,
            ).strip(),
        )
        type_str = (
            (Path("my_project") / "defs" / "my_sling_sync" / "component.yaml")
            .read_text()
            .split("\n")[0]
        )
        create_file(
            file_path=Path("my_project") / "defs" / "my_sling_sync" / "component.yaml",
            contents=format_multiline(f"""
                {type_str}

                attributes:
                  sling:
                    connections:
                      - name: DUCKDB
                        type: duckdb
                        instance: /tmp/jaffle_platform.duckdb
                  replications:
                    - path: replication.yaml
                """),
        )
        _run_command("dagster asset materialize --select '*' -m my_project.definitions")

        # Add debug logic
        create_file(
            component_py_path,
            contents=format_multiline(
                """
                from collections.abc import Iterator

                from dagster_sling import (
                    SlingReplicationCollectionComponent,
                    SlingReplicationSpecModel,
                    SlingResource,
                )

                import dagster as dg


                class CustomSlingReplicationComponent(SlingReplicationCollectionComponent):
                    def execute(
                        self,
                        context: dg.AssetExecutionContext,
                        sling: SlingResource,
                        replication_spec_model: SlingReplicationSpecModel,
                    ) -> Iterator:
                        context.log.info("*******************CUSTOM*************************")
                        return sling.replicate(context=context, debug=True)

                """
            ),
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-component.py",
        )

        # Validate works properly
        _run_command("dagster asset materialize --select '*' -m my_project.definitions")

        # Add custom scope
        create_file(
            component_py_path,
            contents=format_multiline(
                """
                from collections.abc import Mapping
                from typing import Any

                from dagster_sling import SlingReplicationCollectionComponent

                import dagster as dg


                class CustomSlingReplicationComponent(SlingReplicationCollectionComponent):
                    @classmethod
                    def get_additional_scope(cls) -> Mapping[str, Any]:
                        def _custom_cron(cron_schedule: str) -> dg.AutomationCondition:
                            return (
                                dg.AutomationCondition.on_cron(cron_schedule)
                                & ~dg.AutomationCondition.in_progress()
                            )

                        return {"custom_cron": _custom_cron}

                """
            ),
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-component.py",
        )
        # Update the component.yaml to use the new scope
        create_file(
            Path("my_project") / "defs" / "my_sling_sync" / "component.yaml",
            contents=format_multiline(f"""
                {type_str}

                attributes:
                  sling:
                    connections:
                      - name: DUCKDB
                        type: duckdb
                        instance: /tmp/jaffle_platform.duckdb
                  replications:
                    - path: replication.yaml
                  asset_post_processors:
                    - attributes:
                        automation_condition: "{{{{ custom_cron('@daily') }}}}"
                """),
            snippet_path=SNIPPETS_DIR
            / component_type
            / f"{get_next_snip_number()}-component.yaml",
            snippet_replace_regex=[
                (r".*sling:.*\n.*\n.*\n.*\n.*\n", ""),
            ],
        )
        # Validate works properly
        _run_command("dagster asset materialize --select '*' -m my_project.definitions")
