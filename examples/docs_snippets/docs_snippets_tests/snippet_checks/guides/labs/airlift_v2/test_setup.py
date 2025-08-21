from contextlib import ExitStack
from pathlib import Path

from dagster_dg_core.utils import activate_venv

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_PLUGIN_CACHE_REBUILD,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    compare_tree_output,
    isolated_snippet_generation_environment,
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
    with ExitStack() as stack:
        context = stack.enter_context(
            isolated_snippet_generation_environment(
                should_update_snippets=update_snippets,
                snapshot_base_dir=SNIPPETS_DIR / "setup" / "basic_auth",
            )
        )
        _run_command(
            cmd=f"create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project && uv add --editable {EDITABLE_DIR / 'dagster-airlift[core]'}",
        )

        stack.enter_context(activate_venv(".venv"))

        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster_airlift.core.components.AirflowInstanceComponent airflow --name my_airflow --auth-type basic_auth",
            snippet_path=f"{context.get_next_snip_number()}-scaffold.txt",
            snippet_replace_regex=[
                MASK_MY_PROJECT,
                MASK_PLUGIN_CACHE_REBUILD,
                MASK_VENV,
            ],
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name my-project.egg-info -exec rm -r {} \+")
        context.run_command_and_snippet_output(
            cmd="tree src/my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.run_command_and_snippet_output(
            cmd="cat src/my_project/defs/airflow/defs.yaml",
            snippet_path=f"{context.get_next_snip_number()}-cat.txt",
        )

        if not update_snippets:
            _run_command("dg check yaml --no-validate-requirements")


def test_component_files() -> None:
    """Ensures that our example component yaml files have valid syntax.
    Really this should be pytest parametrized but I wanted to reuse the environment and I was too lazy to create a fixture.
    """
    with isolated_snippet_generation_environment(
        should_update_snippets=False,
        snapshot_base_dir=Path("/tmp"),
    ):
        _run_command(
            cmd=f"create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project && uv add --editable {EDITABLE_DIR / 'dagster-airlift[core]'}",
        )
        _run_command(
            cmd="dg scaffold defs dagster_airlift.core.components.AirflowInstanceComponent airflow --name my_airflow --auth-type basic_auth",
        )

        component_yaml_path = (
            Path.cwd() / "src" / "my_project" / "defs" / "airflow" / "defs.yaml"
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
