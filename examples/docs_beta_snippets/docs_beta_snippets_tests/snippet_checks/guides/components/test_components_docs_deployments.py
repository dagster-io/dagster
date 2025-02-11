import os
import re
import subprocess
from tempfile import TemporaryDirectory

import pytest

from dagster._utils.env import environ
from docs_beta_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_EDITABLE_DAGSTER,
)
from docs_beta_snippets_tests.snippet_checks.utils import (
    _run_command,
    check_file,
    compare_tree_output,
    create_file,
    re_ignore_after,
    re_ignore_before,
    run_command_and_snippet_output,
)

COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_beta_snippets"
    / "docs_beta_snippets"
    / "guides"
    / "components"
    / "deployments"
)
MASK_MY_DEPLOYMENT = (r"\/.*?\/my-deployment", "/.../my-deployment")


def test_components_docs_deployments(update_snippets: bool) -> None:
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
                "VIRTUAL_ENV": "",
            }
        ),
    ):
        os.chdir(tempdir)

        # Scaffold deployment
        run_command_and_snippet_output(
            cmd="dg deployment scaffold my-deployment",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-deployment-scaffold.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_DEPLOYMENT],
        )

        # Validate scaffolded files
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        run_command_and_snippet_output(
            cmd="cd my-deployment && tree",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )
        check_file(
            "pyproject.toml",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-pyproject.toml",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                re_ignore_before("[tool.dagster]"),
                re_ignore_after("is_component_lib = true"),
            ],
        )

        # Scaffold code location
        run_command_and_snippet_output(
            cmd="dg code-location scaffold code-location-1 --use-editable-dagster",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-code-location-scaffold.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_EDITABLE_DAGSTER,
                MASK_MY_DEPLOYMENT,
                (r"\nUsing[\s\S]*", "\n..."),
            ],
        )

        # Validate scaffolded files
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name code_location_1.egg-info -exec rm -r {} \+")
        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-tree.txt",
            update_snippets=update_snippets,
            # Remove --sort size from tree output, sadly OSX and Linux tree
            # sort differently when using alpha sort
            snippet_replace_regex=[
                (r"\d+ directories, \d+ files", "..."),
            ],
            custom_comparison_fn=compare_tree_output,
        )

        # Validate code location toml
        check_file(
            "code_locations/code-location-1/pyproject.toml",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-code-location-pyproject.toml",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                re_ignore_before("[tool.dagster]"),
                re_ignore_after("is_component_lib = true"),
            ],
        )

        # Check component types
        run_command_and_snippet_output(
            cmd="cd code_locations/code-location-1 && dg component-type list",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-component-type-list.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_DEPLOYMENT],
        )
        _run_command(
            f"uv add sling_mac_arm64 && uv add --editable '{EDITABLE_DIR / 'dagster-sling'!s}' && uv add --editable '{EDITABLE_DIR / 'dagster-components'!s}[sling]'"
        )
        run_command_and_snippet_output(
            cmd="dg component-type list",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-component-type-list.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_DEPLOYMENT],
        )

        # Scaffold new code location
        run_command_and_snippet_output(
            cmd="cd ../.. && dg code-location scaffold code-location-2 --use-editable-dagster",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-code-location-scaffold.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_EDITABLE_DAGSTER,
                MASK_MY_DEPLOYMENT,
                (r"\nUsing[\s\S]*", "\n..."),
            ],
        )

        # List code locations
        run_command_and_snippet_output(
            cmd="dg code-location list",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-code-location-list.txt",
            update_snippets=update_snippets,
        )

        # Check component types in new code location
        run_command_and_snippet_output(
            cmd="cd code_locations/code-location-2 && dg component-type list",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-component-type-list.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_DEPLOYMENT],
        )

        # Create workspace.yaml file
        _run_command("cd ../../")
        create_file(
            "workspace.yaml",
            """load_from:
  - python_file:
      relative_path: code_locations/code-location-1/code_location_1/definitions.py
      location_name: code_location_1
      executable_path: code_locations/code-location-1/.venv/bin/python
  - python_file:
      relative_path: code_locations/code-location-2/code_location_2/definitions.py
      location_name: code_location_2
      executable_path: code_locations/code-location-2/.venv/bin/python
""",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-workspace.yaml",
        )

        # Ensure dagster loads
        output = _run_command("uv tool run dagster definitions validate")
        assert "Validation successful for code location code_location_1" in output
        assert "Validation successful for code location code_location_2" in output
