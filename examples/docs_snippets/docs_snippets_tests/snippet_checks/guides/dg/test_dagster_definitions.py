from pathlib import Path

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
)

MASK_MY_PROJECT = (r" \/.*?\/my-project", " /.../my-project")
MASK_VENV = (r"Using.*\.venv.*", "")


SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "dg"
    / "dagster-definitions"
)


def test_components_docs_migrating_definitions(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment() as get_next_snip_number:
        _run_command(
            cmd="dg scaffold project my-project --use-editable-dagster && cd my-project",
        )
        _run_command(cmd="uv venv")
        _run_command(cmd="uv sync")
        _run_command(
            f"uv add --editable '{DAGSTER_ROOT / 'python_modules' / 'dagster'!s}' '{DAGSTER_ROOT / 'python_modules' / 'dagster-webserver'!s}'"
        )

        run_command_and_snippet_output(
            cmd="dg scaffold dagster.asset assets/my_asset.py",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-scaffold.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_PROJECT],
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")
        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        run_command_and_snippet_output(
            cmd="cat src/my_project/defs/assets/my_asset.py",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-cat.txt",
            update_snippets=update_snippets,
        )

        create_file(
            Path("src") / "my_project" / "defs" / "assets" / "my_asset.py",
            format_multiline('''
                import dagster as dg


                @dg.asset(group_name="my_group")
                def my_asset(context: dg.AssetExecutionContext) -> None:
                    """Asset that greets you."""
                    context.log.info("hi!")
            '''),
            SNIPPETS_DIR / f"{get_next_snip_number()}-written-asset.py",
        )

        run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_VENV],
        )

        # validate loads
        _run_command(
            "uv pip freeze && uv run dagster asset materialize --select '*' -m 'my_project.definitions'"
        )
