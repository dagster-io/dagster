import os
import re
import subprocess
from tempfile import TemporaryDirectory

from dagster._utils.env import environ
from docs_beta_snippets_tests.snippet_checks.guides.components.utils import DAGSTER_ROOT
from docs_beta_snippets_tests.snippet_checks.utils import (
    _run_command,
    check_file,
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
MASK_MY_DEPLOYMENT = (r" \/.*?\/my-deployment", " /.../my-deployment")


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
            }
        ),
    ):
        os.chdir(tempdir)
        subprocess.check_call(["uv", "pip", "install", "dg"])

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
            cmd="dg code-location scaffold code-location-1",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-code-location-scaffold.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_MY_DEPLOYMENT,
                (r"\nUsing[\s\S]*", "\n..."),
            ],
        )

        # Validate scaffolded files
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name code_location_1.egg-info -exec rm -r {} \+")
        run_command_and_snippet_output(
            cmd="tree --sort size --dirsfirst",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-tree.txt",
            update_snippets=update_snippets,
            # Remove --sort size from tree output, sadly OSX and Linux tree
            # sort differently when using alpha sort
            snippet_replace_regex=[
                ("--sort size --dirsfirst", ""),
                (r"\d+ directories, \d+ files", "..."),
            ],
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
        )
        components_dir = str(
            DAGSTER_ROOT / "python_modules" / "libraries" / "dagster-components"
        )
        _run_command(
            f"uv add sling_mac_arm64 && uv add --editable '{components_dir}[sling]'"
        )
        run_command_and_snippet_output(
            cmd="dg component-type list",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-component-type-list.txt",
            update_snippets=update_snippets,
        )

        # Scaffold new code location
        run_command_and_snippet_output(
            cmd="cd ../.. && dg code-location scaffold code-location-2",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-code-location-scaffold.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
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
