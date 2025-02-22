from pathlib import Path

from dagster._utils.env import environ
from docs_beta_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    isolated_snippet_generation_environment,
)
from docs_beta_snippets_tests.snippet_checks.utils import (
    _run_command,
    check_file,
    create_file,
    run_command_and_snippet_output,
    screenshot_page,
)

MASK_MY_COMPONENT_LIBRARY = (
    r" \/.*?\/my-component-library",
    " /.../my-component-library",
)


COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_beta_snippets"
    / "docs_beta_snippets"
    / "guides"
    / "components"
    / "shell-script-component"
)


def test_components_docs_index(
    update_snippets: bool, update_screenshots: bool, get_selenium_driver
) -> None:
    with isolated_snippet_generation_environment() as get_next_snip_number:
        # Scaffold code location
        _run_command(
            cmd="dg scaffold project my-component-library --use-editable-dagster && cd my-component-library",
        )

        #########################################################
        # Scaffolding a new component type                      #
        #########################################################

        # Scaffold new component type
        run_command_and_snippet_output(
            cmd="dg scaffold component-type shell_command",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-scaffold-shell-command.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_COMPONENT_LIBRARY],
        )

        # Validate scaffolded files
        check_file(
            Path("my_component_library") / "lib" / "shell_command.py",
            COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-shell-command-empty.py",
            update_snippets=update_snippets,
        )

        # Add config schema
        create_file(
            Path("my_component_library") / "lib" / "shell_command.py",
            contents=(COMPONENTS_SNIPPETS_DIR / "with-config-schema.py").read_text(),
        )
        # Sanity check that the component type is registered properly
        _run_command("dg list component-type")

        # Add build defs
        create_file(
            Path("my_component_library") / "lib" / "shell_command.py",
            contents=(COMPONENTS_SNIPPETS_DIR / "with-build-defs.py").read_text(),
        )

        #########################################################
        # Component registration                                #
        #########################################################

        run_command_and_snippet_output(
            cmd="dg list component-type",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-list-component-types.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_COMPONENT_LIBRARY],
        )

        run_command_and_snippet_output(
            cmd="dg docs component-type shell_command@my_component_library --output cli > docs.html",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-component-type-docs.txt",
            update_snippets=update_snippets,
            ignore_output=True,
            snippet_replace_regex=[("--output cli > docs.html", "")],
        )

        check_file(
            Path("docs.html"),
            COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-component-type-docs.html",
            update_snippets=update_snippets,
        )

        # Open the docs in the browser
        screenshot_page(
            get_selenium_driver,
            "file://" + str(Path("docs.html").absolute()),
            DAGSTER_ROOT
            / "docs"
            / "static"
            / "images"
            / "guides"
            / "build"
            / "projects-and-components"
            / "components"
            / "component-type-docs.png",
            update_screenshots=update_screenshots,
        )

        #########################################################
        # Test component we use in docs                         #
        #########################################################

        # We'll create an instance of the component type
        # and e2e test that the component is written correctly, e.g.
        # that we can actually run a shell script.
        create_file(
            Path("my_component_library") / "lib" / "shell_command.py",
            contents=(COMPONENTS_SNIPPETS_DIR / "with-scaffolder.py").read_text(),
        )
        run_command_and_snippet_output(
            cmd="dg scaffold component 'shell_command@my_component_library' my_shell_command",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffold-instance-of-component.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_COMPONENT_LIBRARY],
        )

        check_file(
            Path("my_component_library")
            / "components"
            / "my_shell_command"
            / "component.yaml",
            COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffolded-component.yaml",
            update_snippets=update_snippets,
        )
        check_file(
            Path("my_component_library")
            / "components"
            / "my_shell_command"
            / "script.sh",
            COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffolded-component-script.sh",
            update_snippets=update_snippets,
        )
        _run_command(
            "dagster asset materialize --select '*' -m my_component_library.definitions"
        )
