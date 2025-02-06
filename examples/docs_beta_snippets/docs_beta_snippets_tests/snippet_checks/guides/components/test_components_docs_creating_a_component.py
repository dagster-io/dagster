import os
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from dagster._utils.env import environ
from docs_beta_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_EDITABLE_DAGSTER,
    MASK_JAFFLE_PLATFORM,
    MASK_SLING_DOWNLOAD_DUCKDB,
    MASK_SLING_PROMO,
    MASK_SLING_WARNING,
    MASK_TIME,
)
from docs_beta_snippets_tests.snippet_checks.utils import (
    _run_command,
    check_file,
    compare_tree_output,
    create_file,
    re_ignore_after,
    re_ignore_before,
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


def test_components_docs_index(update_snippets: bool, get_selenium_driver) -> None:
    snip_no = 0

    def next_snip_no():
        nonlocal snip_no
        snip_no += 1
        return snip_no

    with (
        TemporaryDirectory() as tempdir,
        environ(
            {
                "COLUMNS": "90",
                "NO_COLOR": "1",
                "HOME": "/tmp",
                "DAGSTER_GIT_REPO_DIR": str(DAGSTER_ROOT),
            }
        ),
    ):
        os.chdir(tempdir)

        # Scaffold code location
        _run_command(
            cmd="dg code-location scaffold my-component-library --use-editable-dagster && cd my-component-library",
        )

        #########################################################
        # Scaffolding a new component type                      #
        #########################################################

        # Scaffold new component type
        run_command_and_snippet_output(
            cmd="dg component-type scaffold shell_command",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-scaffold-shell-command.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_COMPONENT_LIBRARY],
        )

        # Validate scaffolded files
        check_file(
            Path("my_component_library") / "lib" / "shell_command.py",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-shell-command-empty.py",
            update_snippets=update_snippets,
        )

        # Add config schema
        create_file(
            Path("my_component_library") / "lib" / "shell_command.py",
            contents=(COMPONENTS_SNIPPETS_DIR / "with-config-schema.py").read_text(),
        )
        # Sanity check that the component type is registered properly
        _run_command("dg component-type list")

        # Add build defs
        create_file(
            Path("my_component_library") / "lib" / "shell_command.py",
            contents=(COMPONENTS_SNIPPETS_DIR / "with-build-defs.py").read_text(),
        )

        #########################################################
        # Component registration                                #
        #########################################################

        run_command_and_snippet_output(
            cmd="dg component-type list",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-list-component-types.txt",
            update_snippets=update_snippets,
        )

        run_command_and_snippet_output(
            cmd="dg component-type docs shell_command@my_component_library --output cli > docs.html",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-component-type-docs.txt",
            update_snippets=update_snippets,
            ignore_output=True,
            snippet_replace_regex=[("--output cli > docs.html", "")],
        )

        check_file(
            Path("docs.html"),
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-dg-component-type-docs.html",
            update_snippets=update_snippets,
        )

        # Open the docs in the browser
        screenshot_page(
            get_selenium_driver,
            "file://" + str(Path("docs.html").absolute()),
            DAGSTER_ROOT
            / "docs"
            / "docs-beta"
            / "static"
            / "images"
            / "guides"
            / "build"
            / "projects-and-components"
            / "components"
            / "component-type-docs.png",
            update_snippets=update_snippets,
        )

        #########################################################
        # Test component we use in docs                         #
        #########################################################

        # We'll create an instance of the component type
        # and e2e test that the component is written correctly, e.g.
        # that we can actually run a shell script.
        _run_command(
            cmd="dg component scaffold 'shell_command@my_component_library' my_shell_command",
        )
        check_file(
            Path("my_component_library")
            / "components"
            / "my_shell_command"
            / "component.yaml",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-scaffolded-component.yaml",
            update_snippets=update_snippets,
        )
        (
            Path("my_component_library")
            / "components"
            / "my_shell_command"
            / "component.yaml"
        ).write_text("""type: shell_command@my_component_library

params:
  script_path: script.sh
  asset_attributes:
    key: my_shell_command
""")
        Path("my_component_library/components/my_shell_command/script.sh").write_text(
            """#!/bin/bash
echo "Hello, world!"
"""
        )
        _run_command(
            "dagster asset materialize --select '*' -m my_component_library.definitions"
        )
