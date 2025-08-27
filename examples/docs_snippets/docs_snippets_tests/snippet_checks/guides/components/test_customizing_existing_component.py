import textwrap
from contextlib import ExitStack
from pathlib import Path

import pytest
from dagster_dg_core.utils import activate_venv

from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    format_multiline,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    compare_tree_output,
    isolated_snippet_generation_environment,
    screenshot_page,
)

MASK_MY_PROJECT = (r" \/.*?\/my-project", " /.../my-project")


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
    with ExitStack() as stack:
        context = stack.enter_context(
            isolated_snippet_generation_environment(
                should_update_snippets=update_snippets,
                snapshot_base_dir=SNIPPETS_DIR,
                global_snippet_replace_regexes=[
                    MASK_MY_PROJECT,
                ],
                # For multi-parameter tests which share snippets, we don't want to clear the
                # snapshot dir before updating the snippets
                clear_snapshot_dir_before_update=False,
            )
        )

        # Scaffold code location, add some assets
        context.run_command_and_snippet_output(
            cmd=textwrap.dedent(
                f"""\
                create-dagster project my-project --uv-sync --use-editable-dagster \\
                    && source my-project/.venv/bin/activate \\
                    && cd my-project/src \\
                    && uv add --editable {EDITABLE_DIR / "dagster-sling"} \\
                    && dg scaffold defs dagster_sling.SlingReplicationCollectionComponent my_sling_sync\
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("--editable.*dagster-sling", "dagster-sling"),
                (".*&& source my-project/.venv/bin/activate.*\n", ""),
                ("create-dagster", "uvx-U create-dagster"),
            ],
            ignore_output=True,
        )

        stack.enter_context(activate_venv("../.venv"))

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        if component_type == "local":
            component_py_path = (
                Path("my_project") / "defs" / "my_sling_sync" / "component.py"
            )
            context.create_file(
                component_py_path,
                contents=CUSTOM_SLING_COMPONENT_BODY,
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{context.get_next_snip_number()}-component.py",
            )
            _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
            _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")
            context.run_command_and_snippet_output(
                cmd="tree my_project",
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{context.get_next_snip_number()}-tree.txt",
                custom_comparison_fn=compare_tree_output,
            )
            context.create_file(
                Path("my_project") / "defs" / "my_sling_sync" / "defs.yaml",
                contents=(Path("my_project") / "defs" / "my_sling_sync" / "defs.yaml")
                .read_text()
                .replace(
                    "dagster_sling.SlingReplicationCollectionComponent",
                    "my_project.defs.my_sling_sync.component.CustomSlingReplicationComponent",
                ),
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{context.get_next_snip_number()}-defs.yaml",
            )
            context.get_next_snip_number()
        elif component_type == "global":
            component_py_path = (
                Path("my_project")
                / "components"
                / "custom_sling_replication_component.py"
            )
            context.run_command_and_snippet_output(
                cmd="dg scaffold component CustomSlingReplicationComponent",
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{context.get_next_snip_number()}-scaffold-component.txt",
            )
            context.create_file(
                component_py_path,
                contents=CUSTOM_SLING_COMPONENT_BODY,
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{context.get_next_snip_number()}-component.py",
            )
            _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
            _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")
            context.run_command_and_snippet_output(
                cmd="tree my_project",
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{context.get_next_snip_number()}-tree.txt",
                custom_comparison_fn=compare_tree_output,
            )
            context.create_file(
                Path("my_project") / "defs" / "my_sling_sync" / "defs.yaml",
                contents=(Path("my_project") / "defs" / "my_sling_sync" / "defs.yaml")
                .read_text()
                .replace(
                    "dagster_sling.SlingReplicationCollectionComponent",
                    "my_project.components.custom_sling_replication_component.CustomSlingReplicationComponent",
                ),
                snippet_path=SNIPPETS_DIR
                / component_type
                / f"{context.get_next_snip_number()}-defs.yaml",
            )

        if not update_snippets:
            _run_command("dg check yaml")

        # Set up DuckDB to run, verify everything works ok
        _run_command(
            cmd=textwrap.dedent("""
                curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv &&
                curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv &&
                curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv
            """).strip(),
        )
        context.create_file(
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
            (Path("my_project") / "defs" / "my_sling_sync" / "defs.yaml")
            .read_text()
            .split("\n")[0]
        )
        context.create_file(
            file_path=Path("my_project") / "defs" / "my_sling_sync" / "defs.yaml",
            contents=format_multiline(f"""
                {type_str}

                attributes:
                  connections:
                    DUCKDB:
                      type: duckdb
                      instance: /tmp/jaffle_platform.duckdb
                  replications:
                    - path: replication.yaml
                """),
        )
        if not update_snippets:
            _run_command("dg launch --assets '*'")

        # Add debug logic
        context.create_file(
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
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-component.py",
        )

        # Validate works properly
        if not update_snippets:
            _run_command("dg launch --assets '*'")

        # Add custom scope
        context.create_file(
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
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-component.py",
        )
        # Update the component.yaml to use the new scope
        context.create_file(
            Path("my_project") / "defs" / "my_sling_sync" / "defs.yaml",
            contents=format_multiline(f"""
                {type_str}

                attributes:
                  connections:
                    DUCKDB:
                      type: duckdb
                      instance: /tmp/jaffle_platform.duckdb
                  replications:
                    - path: replication.yaml
                post_processing:
                  assets:
                    - attributes:
                        automation_condition: "{{{{ custom_cron('@daily') }}}}"
                """),
            snippet_path=SNIPPETS_DIR
            / component_type
            / f"{context.get_next_snip_number()}-defs.yaml",
            snippet_replace_regex=[
                (r".*sling:.*\n.*\n.*\n.*\n.*\n", ""),
            ],
        )
        # Validate works properly
        if not update_snippets:
            _run_command("dg launch --assets '*'")
