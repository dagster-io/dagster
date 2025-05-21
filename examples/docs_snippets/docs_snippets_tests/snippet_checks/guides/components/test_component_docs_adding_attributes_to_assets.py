import textwrap
from pathlib import Path

from dagster._utils.env import environ
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
)


def test_components_docs_adding_attributes_to_assets(
    update_snippets: bool, update_screenshots: bool, get_selenium_driver
) -> None:
    with isolated_snippet_generation_environment(
        should_update_snippets=update_snippets
    ) as context:
        # Scaffold code location, add some assets
        context.run_command_and_snippet_output(
            cmd=textwrap.dedent(
                """\
                dg scaffold project my-project --python-environment uv_managed --use-editable-dagster \\
                    && cd my-project/src \\
                    && dg scaffold dagster.asset team_a/subproject/a.py \\
                    && dg scaffold dagster.asset team_a/b.py \\
                    && dg scaffold dagster.asset team_b/c.py\
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--python-environment uv_managed --use-editable-dagster ", "")
            ],
            ignore_output=True,
        )
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name my_project.egg-info -exec rm -r {} \+")

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        # List defs
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-list-defs.txt",
            snippet_replace_regex=[MASK_VENV, MASK_USING_LOG_MESSAGE],
        )

        # Add component.yaml
        context.create_file(
            Path("my_project") / "defs" / "team_a" / "component.yaml",
            contents=(SNIPPETS_DIR / "component.yaml").read_text(),
        )

        # Tree the project
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        # List defs
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-list-defs.txt",
            snippet_replace_regex=[MASK_VENV, MASK_USING_LOG_MESSAGE],
        )
