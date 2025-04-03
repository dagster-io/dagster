from pathlib import Path

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
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

MASK_MY_EXISTING_PROJECT = (r" \/.*?\/my-existing-project", " /.../my-existing-project")
MASK_VENV = (r"Using.*\.venv.*", "")
MASK_USING_LOG_MESSAGE = (r"Using.*\n", "")

SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "components"
    / "adding-attributes-to-assets"
)


def test_components_docs_adding_attributes_to_assets(
    update_snippets: bool, update_screenshots: bool, get_selenium_driver
) -> None:
    with isolated_snippet_generation_environment() as get_next_snip_number:
        # Scaffold code location, add some assets
        _run_command(
            cmd="dg scaffold project my-project --use-editable-dagster && cd my-project/src",
        )
        _run_command(
            cmd="dg scaffold dagster.asset team_a/subproject/a.py",
        )
        _run_command(
            cmd="dg scaffold dagster.asset team_a/b.py",
        )
        _run_command(
            cmd="dg scaffold dagster.asset team_b/c.py",
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

        # List defs
        run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_VENV, MASK_USING_LOG_MESSAGE],
        )

        # Add component.yaml
        create_file(
            Path("my_project") / "defs" / "team_a" / "component.yaml",
            contents=(SNIPPETS_DIR / "component.yaml").read_text(),
        )

        # Tree the project
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        # List defs
        run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_VENV, MASK_USING_LOG_MESSAGE],
        )
