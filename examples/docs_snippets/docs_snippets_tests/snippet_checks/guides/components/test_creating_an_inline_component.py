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
    / "creating-an-inline-component"
    / "generated"
)


def test_creating_an_inline_component(
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
            cmd="dg scaffold defs inline-component --typename AssetWithSchedule assets_with_schedules",
            snippet_path=f"{context.get_next_snip_number()}-dg-scaffold-defs-inline-component.txt",
        )

        # Validate scaffolded files
        context.check_file(
            Path("src")
            / "my_project"
            / "defs"
            / "assets_with_schedules"
            / "asset_with_schedule.py",
            f"{context.get_next_snip_number()}-asset-with-schedule-init.py",
        )

        context.check_file(
            Path("src") / "my_project" / "defs" / "assets_with_schedules" / "defs.yaml",
            f"{context.get_next_snip_number()}-assets-with-schedules-defs-init.yaml",
        )

        # Modified scaffolded component
        context.create_file(
            Path("src")
            / "my_project"
            / "defs"
            / "assets_with_schedules"
            / "asset_with_schedule.py",
            contents=(
                COMPONENTS_SNIPPETS_DIR.parent / "asset-with-schedule-final.py"
            ).read_text(),
        )

        # Modified scaffolded component
        context.create_file(
            Path("src") / "my_project" / "defs" / "assets_with_schedules" / "defs.yaml",
            contents=(
                COMPONENTS_SNIPPETS_DIR.parent / "assets-with-schedules-defs-final.yaml"
            ).read_text(),
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-dg-list-defs.txt",
        )
