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
    _run_command,
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
    / "dbt-component"
)


def test_components_docs_dbt_project(
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
        ExitStack() as stack,
    ):
        # Scaffold code location
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("--editable.*dagster-dbt", "dagster-dbt"),
            ],
            ignore_output=True,
        )

        stack.enter_context(activate_venv(".venv"))
        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-dbt'} && uv add dbt-duckdb",
            snippet_path=f"{context.get_next_snip_number()}-add-dbt.txt",
            print_cmd="uv add dagster-dbt dbt-duckdb",
            ignore_output=True,
        )

        # Clone jaffle shop dbt project
        context.run_command_and_snippet_output(
            cmd="git clone --depth=1 https://github.com/dbt-labs/jaffle_shop.git dbt && rm -rf dbt/.git",
            snippet_path=f"{context.get_next_snip_number()}-jaffle-clone.txt",
            ignore_output=True,
        )

        # Create profiles.yml for DuckDB configuration
        context.create_file(
            Path("dbt") / "profiles.yml",
            contents=textwrap.dedent(
                """\
                jaffle_shop:
                  target: dev
                  outputs:
                    dev:
                      type: duckdb
                      path: tutorial.duckdb
                      threads: 24
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-profiles.yml",
        )

        # scaffold dbt component
        context.run_command_and_snippet_output(
            cmd='dg scaffold defs dagster_dbt.DbtProjectComponent dbt_ingest \\\n  --project-path "dbt"',
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-dbt-component.txt",
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree src/my_project",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("src") / "my_project" / "defs" / "dbt_ingest" / "defs.yaml",
            snippet_path=f"{context.get_next_snip_number()}-component.yaml",
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Test dbt run
        context.run_command_and_snippet_output(
            cmd="dg launch --assets '*'",
            snippet_path=f"{context.get_next_snip_number()}-dbt-run.txt",
            ignore_output=True,
        )

        # Update component.yaml with model selector
        context.create_file(
            Path("src") / "my_project" / "defs" / "dbt_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_dbt.DbtProjectComponent

                attributes:
                  project: '{{ project_root }}/dbt'
                  select: "customers"
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
            Path("src") / "my_project" / "defs" / "dbt_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_dbt.DbtProjectComponent

                attributes:
                  project: '{{ project_root }}/dbt'
                  select: "customers"
                  translation:
                    group_name: dbt_models
                    description: "Transforms data using dbt model {{ node.name }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Test dbt run
        _run_command(
            cmd="dg launch --assets '*'",
        )

        # scaffold a PythonScriptComponent
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster.PythonScriptComponent my_python_script",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-python-script-component.txt",
        )
        context.run_command_and_snippet_output(
            cmd="touch src/my_project/defs/my_python_script/export_customers.py",
            snippet_path=f"{context.get_next_snip_number()}-touch-export-customers.txt",
        )

        context.create_file(
            Path("src") / "my_project" / "defs" / "my_python_script" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster.PythonScriptComponent

                attributes:
                  execution:
                    path: my_script.py
                  assets:
                    - key: customers_export
                      deps:
                        - "{{ load_component_at_path('dbt_ingest').asset_key_for_model('customers') }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-component.yaml",
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )
