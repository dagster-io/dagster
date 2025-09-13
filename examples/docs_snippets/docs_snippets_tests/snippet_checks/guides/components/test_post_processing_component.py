import textwrap
from contextlib import ExitStack
from pathlib import Path

from dagster_dg_core.utils import activate_venv

from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    MASK_PLUGIN_CACHE_REBUILD,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    isolated_snippet_generation_environment,
)

MASK_MY_COMPONENT_LIBRARY = (
    r" \/.*?\/my-project",
    " /.../my-project",
)


COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "components"
    / "post-processing-components"
    / "generated"
)


def test_post_processing_component(
    update_snippets: bool,
) -> None:
    with ExitStack() as stack:
        context = stack.enter_context(
            isolated_snippet_generation_environment(
                should_update_snippets=update_snippets,
                snapshot_base_dir=COMPONENTS_SNIPPETS_DIR,
                global_snippet_replace_regexes=[
                    MASK_MY_COMPONENT_LIBRARY,
                    MASK_PLUGIN_CACHE_REBUILD,
                ],
            )
        )

        # Scaffold code location
        _run_command(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project",
        )

        stack.enter_context(activate_venv(".venv"))

        #########################################################
        # Scaffolding a new component type                      #
        #########################################################

        # Scaffold new component type
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs DefsFolderComponent my_assets",
            snippet_path=f"{context.get_next_snip_number()}-dg-scaffold-defs-my-assets.txt",
        )

        # Validate scaffolded files
        context.check_file(
            Path("src") / "my_project" / "defs" / "my_assets" / "defs.yaml",
            f"{context.get_next_snip_number()}-my-assets-defs-1.yaml",
        )

        # Add asset defs
        for name in ["foo", "bar"]:
            context.create_file(
                Path("src") / "my_project" / "defs" / "my_assets" / f"{name}.py",
                contents=(COMPONENTS_SNIPPETS_DIR.parent / f"{name}.py").read_text(),
            )

        # Scaffold new component type
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-dg-list-defs-1.txt",
        )

        # Modified scaffolded component
        context.create_file(
            Path("src") / "my_project" / "defs" / "my_assets" / "defs.yaml",
            contents=(
                COMPONENTS_SNIPPETS_DIR.parent / "my-assets-defs-2.yaml"
            ).read_text(),
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-dg-list-defs-2.txt",
        )

        context.create_file(
            Path("src") / "my_project" / "defs" / "my_assets" / "defs.yaml",
            contents=(
                COMPONENTS_SNIPPETS_DIR.parent / "my-assets-defs-3.yaml"
            ).read_text(),
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-dg-list-defs-3.txt",
        )
