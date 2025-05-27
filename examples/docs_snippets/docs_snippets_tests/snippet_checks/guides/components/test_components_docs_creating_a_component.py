from contextlib import ExitStack
from pathlib import Path

from dagster_dg.cli.utils import activate_venv

from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    MASK_PLUGIN_CACHE_REBUILD,
)
from docs_snippets_tests.snippet_checks.utils import (
    isolated_snippet_generation_environment,
)

MASK_MY_COMPONENT_LIBRARY = (
    r" \/.*?\/my-component-library",
    " /.../my-component-library",
)


COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "components"
    / "shell-script-component"
)


def test_creating_a_component(
    update_snippets: bool, update_screenshots: bool, get_selenium_driver
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
        context._run_command(
            cmd="dg scaffold project my-component-library --python-environment uv_managed --use-editable-dagster && cd my-component-library",
        )

        stack.enter_context(activate_venv(".venv"))

        #########################################################
        # Scaffolding a new component type                      #
        #########################################################

        # Scaffold new component type
        context.run_command_and_snippet_output(
            cmd="dg scaffold component ShellCommand",
            snippet_path=f"{context.get_next_snip_number()}-dg-scaffold-shell-command.txt",
        )

        # Validate scaffolded files
        context.check_file(
            Path("src") / "my_component_library" / "components" / "shell_command.py",
            f"{context.get_next_snip_number()}-shell-command-empty.py",
        )

        # Add config schema
        context.create_file(
            Path("src") / "my_component_library" / "components" / "shell_command.py",
            contents=(COMPONENTS_SNIPPETS_DIR / "with-config-schema.py").read_text(),
        )
        # Sanity check that the component type is registered properly
        context._run_command("dg list components")

        # Add build defs
        context.create_file(
            Path("src") / "my_component_library" / "components" / "shell_command.py",
            contents=(COMPONENTS_SNIPPETS_DIR / "with-build-defs.py").read_text(),
        )

        #########################################################
        # Component registration                                #
        #########################################################

        context.run_command_and_snippet_output(
            cmd="dg list components",
            snippet_path=f"{context.get_next_snip_number()}-dg-list-components.txt",
        )

        # Disabled for now, since the new dg docs command does not support output to console

        # context.run_command_and_snippet_output(
        #     cmd="dg docs component-type my_component_library.components.ShellCommand --output cli > docs.html",
        #     snippet_path= f"{context.get_next_snip_number()}-dg-component-type-docs.txt",
        #
        #     ignore_output=True,
        #     snippet_replace_regex=[("--output cli > docs.html", "")],
        # )

        # context.check_file(
        #     Path("docs.html"),
        #     COMPONENTS_SNIPPETS_DIR
        #     / f"{context.get_next_snip_number()}-dg-component-type-docs.html",
        #
        # )

        # # Open the docs in the browser
        # screenshot_page(
        #     get_selenium_driver,
        #     "file://" + str(Path("docs.html").absolute()),
        #     DAGSTER_ROOT
        #     / "docs"
        #     / "static"
        #     / "images"
        #     / "guides"
        #     / "build"
        #     / "projects-and-components"
        #     / "components"
        #     / "component-type-docs.png",
        #     update_screenshots=update_screenshots,
        # )

        #########################################################
        # Test component we use in docs                         #
        #########################################################

        # We'll create an instance of the component type
        # and e2e test that the component is written correctly, e.g.
        # that we can actually run a shell script.
        context.create_file(
            Path("src") / "my_component_library" / "components" / "shell_command.py",
            contents=(COMPONENTS_SNIPPETS_DIR / "with-scaffolder.py").read_text(),
        )
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs 'my_component_library.components.ShellCommand' my_shell_command",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-instance-of-component.txt",
        )

        context.check_file(
            Path("src")
            / "my_component_library"
            / "defs"
            / "my_shell_command"
            / "defs.yaml",
            f"{context.get_next_snip_number()}-scaffolded-defs.yaml",
        )
        context.check_file(
            Path("src")
            / "my_component_library"
            / "defs"
            / "my_shell_command"
            / "script.sh",
            f"{context.get_next_snip_number()}-scaffolded-component-script.sh",
        )
        context._run_command(
            "uv run dagster asset materialize --select '*' -m my_component_library.definitions"
        )
