from pathlib import Path

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_EDITABLE_DAGSTER,
    MASK_USING_ENVIRONMENT,
    format_multiline,
    make_project_path_mask,
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
            cmd="dg scaffold project my-project --use-editable-dagster",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffolding-project.txt",
            snippet_replace_regex=[
                MASK_EDITABLE_DAGSTER,
                MASK_USING_ENVIRONMENT,
                make_project_path_mask("my-project"),
            ],
            print_cmd="dg scaffold project my-project",
            input_str="y\n",
        )
        context.run_tree_command_and_snippet_output(
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
        )
