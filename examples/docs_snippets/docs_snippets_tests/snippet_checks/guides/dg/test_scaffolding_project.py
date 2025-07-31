from pathlib import Path

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    MASK_EDITABLE_DAGSTER,
    MASK_USING_ENVIRONMENT,
    make_project_scaffold_mask,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    compare_tree_output,
    isolated_snippet_generation_environment,
)

SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "dg"
    / "scaffolding-project"
)


def test_dg_docs_scaffolding_project(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment(
        should_update_snippets=update_snippets,
        snapshot_base_dir=SNIPPETS_DIR,
    ) as context:
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --use-editable-dagster",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffolding-project.txt",
            snippet_replace_regex=[
                MASK_EDITABLE_DAGSTER,
                MASK_USING_ENVIRONMENT,
                make_project_scaffold_mask("my-project"),
                ("create-dagster", "uvx create-dagster@latest"),
            ],
            print_cmd="create-dagster project my-project",
            input_str="y\n",
        )
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")
        context.run_command_and_snippet_output(
            cmd="tree",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )
