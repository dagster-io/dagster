from contextlib import ExitStack
from pathlib import Path

from dagster_dg_core.utils import activate_venv

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


def test_components_docs_dbt_project_remote(
    update_snippets: bool,
) -> None:
    """Test that generates snippets for the 'External Git Repository' tab in the dbt component docs.

    This test scaffolds a dbt component with --git-url to generate the remote configuration snippets.
    Note: This test does NOT run `dg list defs` since that would require actually cloning the
    remote repository. The list defs output is shown in the shared section of the docs.
    """
    with (
        isolated_snippet_generation_environment(
            should_update_snippets=update_snippets,
            snapshot_base_dir=SNIPPETS_DIR,
            global_snippet_replace_regexes=[
                MASK_VENV,
                MASK_USING_LOG_MESSAGE,
                MASK_MY_PROJECT,
            ],
            # Don't clear the snapshot dir since we're adding to existing snippets
            clear_snapshot_dir_before_update=False,
        ) as context,
        ExitStack() as stack,
    ):
        # Scaffold code location (same as existing test)
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project",
            snippet_path=None,  # Don't save - already covered by existing test
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("--editable.*dagster-dbt", "dagster-dbt"),
            ],
            ignore_output=True,
        )

        stack.enter_context(activate_venv(".venv"))
        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-dbt'} && uv add dbt-duckdb",
            snippet_path=None,  # Don't save - already covered by existing test
            print_cmd="uv add dagster-dbt dbt-duckdb",
            ignore_output=True,
        )

        # Scaffold dbt component with --git-url for remote repository
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster_dbt.DbtProjectComponent dbt_ingest \\\n"
            '  --git-url "https://github.com/dagster-io/jaffle-platform.git" \\\n'
            '  --project-path "jdbt"',
            snippet_path="remote-1-scaffold-dbt-component.txt",
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")

        # Tree the project (same structure as colocated, but different content in defs.yaml)
        context.run_command_and_snippet_output(
            cmd="tree src/my_project",
            snippet_path="remote-2-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        # Check the generated defs.yaml for remote configuration
        context.check_file(
            Path("src") / "my_project" / "defs" / "dbt_ingest" / "defs.yaml",
            snippet_path="remote-3-component.yaml",
        )
