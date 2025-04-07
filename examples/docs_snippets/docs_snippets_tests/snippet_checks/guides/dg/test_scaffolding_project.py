from pathlib import Path

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_EDITABLE_DAGSTER,
    MASK_USING_ENVIRONMENT,
    format_multiline,
    isolated_snippet_generation_environment,
    make_project_path_mask,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    check_file,
    compare_tree_output,
    create_file,
    run_command_and_snippet_output,
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
    with isolated_snippet_generation_environment() as get_next_snip_number:
        run_command_and_snippet_output(
            cmd="dg init --project-name my-project --use-editable-dagster",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffolding-project.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_EDITABLE_DAGSTER,
                MASK_USING_ENVIRONMENT,
                make_project_path_mask("my-project"),
            ],
        )
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")
        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )
