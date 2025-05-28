from pathlib import Path

import pytest

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_PLUGIN_CACHE_REBUILD,
    format_multiline,
    isolated_snippet_generation_environment,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    compare_tree_output,
    create_file,
    run_command_and_snippet_output,
)

MASK_MY_PROJECT = (r" \/.*?\/my-project", " /.../my-project")
MASK_VENV = (r"Using.*\.venv.*", "")


SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "integrations"
    / "airlift_v2"
)


def test_setup_basic_auth(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment() as get_next_snip_number:
        _run_command(
            cmd=f"dg scaffold project my-project --python-environment uv_managed --use-editable-dagster && cd my-project && uv add --editable {EDITABLE_DIR / 'dagster-airlift[core]'}",
        )

        run_command_and_snippet_output(
            cmd="dg scaffold dagster_airlift.core.components.AirflowInstanceComponent airflow --name my_airflow --auth-type basic_auth",
            snippet_path=SNIPPETS_DIR
            / "setup"
            / "basic_auth"
            / f"{get_next_snip_number()}-scaffold.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_MY_PROJECT,
                MASK_PLUGIN_CACHE_REBUILD,
                MASK_VENV,
            ],
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")
        run_command_and_snippet_output(
            cmd="tree src/my_project/defs",
            snippet_path=SNIPPETS_DIR
            / "setup"
            / "basic_auth"
            / f"{get_next_snip_number()}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        run_command_and_snippet_output(
            cmd="cat src/my_project/defs/airflow/component.yaml",
            snippet_path=SNIPPETS_DIR
            / "setup"
            / "basic_auth"
            / f"{get_next_snip_number()}-cat.txt",
            update_snippets=update_snippets,
        )

        _run_command("dg check yaml --no-validate-requirements")


def test_component_files() -> None:
    """Ensures that our example component yaml files have valid syntax.
    Really this should be pytest parametrized but I wanted to reuse the environment and I was too lazy to create a fixture.
    """
    with isolated_snippet_generation_environment():
        _run_command(
            cmd=f"dg scaffold project my-project --python-environment uv_managed --use-editable-dagster && cd my-project && uv add --editable {EDITABLE_DIR / 'dagster-airlift[core]'}",
        )
        _run_command(
            cmd="dg scaffold dagster_airlift.core.components.AirflowInstanceComponent airflow --name my_airflow --auth-type basic_auth",
        )

        component_yaml_path = (
            Path.cwd() / "src" / "my_project" / "defs" / "airflow" / "component.yaml"
        )

        for path in [
            SNIPPETS_DIR
            / "represent_airflow_dags_in_dagster"
            / "component_dag_mappings.yaml",
            SNIPPETS_DIR
            / "represent_airflow_dags_in_dagster"
            / "component_task_mappings.yaml",
        ]:
            content = path.read_text()
            component_yaml_path.write_text(content)
            _run_command("dg check yaml --no-validate-requirements")
