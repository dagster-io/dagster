import textwrap
from contextlib import ExitStack
from pathlib import Path

from dagster_dg_core.utils import activate_venv

from docs_snippets_tests.snippet_checks.guides.components.utils import DAGSTER_ROOT
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    compare_tree_output,
    isolated_snippet_generation_environment,
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
    / "generated"
)


def test_components_docs_adding_attributes_to_assets(
    update_snippets: bool, update_screenshots: bool, get_selenium_driver
) -> None:
    with ExitStack() as stack:
        context = stack.enter_context(
            isolated_snippet_generation_environment(
                should_update_snippets=update_snippets,
                snapshot_base_dir=SNIPPETS_DIR,
                global_snippet_replace_regexes=[
                    MASK_MY_EXISTING_PROJECT,
                    MASK_VENV,
                    MASK_USING_LOG_MESSAGE,
                ],
            )
        )
        # Scaffold code location, add some assets
        context.run_command_and_snippet_output(
            cmd=textwrap.dedent(
                """\
                create-dagster project my-project --uv-sync --use-editable-dagster \\
                    && source my-project/.venv/bin/activate \\
                    && cd my-project/src \\
                    && dg scaffold defs dagster.asset team_a/subproject/a.py \\
                    && dg scaffold defs dagster.asset team_a/b.py \\
                    && dg scaffold defs dagster.asset team_b/c.py\
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                (".*&& source my-project/.venv/bin/activate.*\n", ""),
                ("create-dagster", "uvx create-dagster@latest"),
            ],
            ignore_output=True,
        )

        stack.enter_context(activate_venv("../.venv"))

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        # List defs
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Add component.yaml
        context.create_file(
            Path("my_project") / "defs" / "team_a" / "defs.yaml",
            contents=(SNIPPETS_DIR.parent / "defs.yaml").read_text(),
        )

        # Tree the project
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        # List defs
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )
