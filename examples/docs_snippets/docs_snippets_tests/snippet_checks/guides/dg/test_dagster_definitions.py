from pathlib import Path

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_PLUGIN_CACHE_REBUILD,
    format_multiline,
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
    / "guides"
    / "dg"
    / "dagster-definitions"
)


def test_dagster_definitions(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment(
        should_update_snippets=update_snippets,
        snapshot_base_dir=SNIPPETS_DIR,
        global_snippet_replace_regexes=[
            MASK_MY_PROJECT,
            MASK_PLUGIN_CACHE_REBUILD,
            MASK_VENV,
        ],
    ) as context:
        _run_command(
            cmd="dg scaffold project my-project --python-environment uv_managed --use-editable-dagster && cd my-project",
        )

        context.run_command_and_snippet_output(
            cmd="dg scaffold dagster.asset assets/my_asset.py",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold.txt",
        )

        context.run_tree_command_and_snippet_output(
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
        )

        context.run_command_and_snippet_output(
            cmd="cat src/my_project/defs/assets/my_asset.py",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-cat.txt",
        )

        context.create_file(
            Path("src") / "my_project" / "defs" / "assets" / "my_asset.py",
            format_multiline('''
                import dagster as dg


                @dg.asset(group_name="my_group")
                def my_asset(context: dg.AssetExecutionContext) -> None:
                    """Asset that greets you."""
                    context.log.info("hi!")
            '''),
            SNIPPETS_DIR / f"{context.get_next_snip_number()}-written-asset.py",
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # validate loads
        _run_command(
            "uv pip freeze && uv run dagster asset materialize --select '*' -m 'my_project.definitions'"
        )
