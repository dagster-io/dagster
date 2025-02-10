import os
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

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
)

MASK_MY_EXISTING_PROJECT = (r" \/.*?\/my-existing-project", " /.../my-existing-project")


COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_beta_snippets"
    / "docs_beta_snippets"
    / "guides"
    / "components"
    / "migrating-definitions"
)


MY_EXISTING_PROJECT = Path(__file__).parent / "my-existing-project"


def test_components_docs_migrating_definitions(update_snippets: bool) -> None:
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

        _run_command(f"cp -r {MY_EXISTING_PROJECT} . && cd my-existing-project")
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(
            r"find . -type d -name my_existing_project.egg-info -exec rm -r {} \+"
        )
        _run_command("mkdir -p my_existing_project/components")

        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        check_file(
            Path("my_existing_project") / "definitions.py",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-definitions-before.py",
            update_snippets=update_snippets,
        )

        check_file(
            Path("my_existing_project") / "elt" / "definitions.py",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-inner-definitions-before.py",
            update_snippets=update_snippets,
        )

        _run_command(cmd="uv venv")
        _run_command(cmd="uv sync")
        _run_command(
            f"uv add --editable '{EDITABLE_DIR / 'dagster-components'!s}' '{DAGSTER_ROOT / 'python_modules' / 'dagster'!s}' '{DAGSTER_ROOT / 'python_modules' / 'dagster-webserver'!s}'"
        )

        run_command_and_snippet_output(
            cmd="dg component scaffold 'definitions@dagster_components' elt-definitions",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-scaffold.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_EXISTING_PROJECT],
        )

        create_file(
            Path("my_existing_project")
            / "components"
            / "elt-definitions"
            / "component.yaml",
            """type: definitions@dagster_components

params:
  definitions_path: definitions.py
""",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-component-yaml.txt",
        )

        run_command_and_snippet_output(
            cmd="mv my_existing_project/elt/definitions.py my_existing_project/components/elt-definitions && rm -rf my_existing_project/elt",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-mv.txt",
            update_snippets=update_snippets,
        )

        create_file(
            Path("my_existing_project") / "definitions.py",
            """from pathlib import Path

import dagster_components as dg_components
from my_existing_project.analytics import definitions as analytics_definitions

import dagster as dg

defs = dg.Definitions.merge(
    dg.load_definitions_from_module(analytics_definitions),
    dg_components.build_component_defs(Path(__file__).parent / "components"),
)
""",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-definitions-after.py",
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(
            r"find . -type d -name my_existing_project.egg-info -exec rm -r {} \+"
        )

        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-tree-after.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        # validate loads
        _run_command(
            "uv run dagster asset materialize --select '*' -m 'my_existing_project.definitions'"
        )
