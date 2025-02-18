import os
from pathlib import Path
from tempfile import TemporaryDirectory

from dagster._utils.env import environ
from docs_beta_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
)
from docs_beta_snippets_tests.snippet_checks.utils import (
    _run_command,
    check_file,
    compare_tree_output,
    create_file,
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
                "VIRTUAL_ENV": "",
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

        run_command_and_snippet_output(
            cmd="mv my_existing_project/elt/* my_existing_project/components/elt-definitions && rm -rf my_existing_project/elt",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-mv.txt",
            update_snippets=update_snippets,
        )

        create_file(
            Path("my_existing_project")
            / "components"
            / "elt-definitions"
            / "definitions.py",
            """import dagster as dg

from . import assets
from .jobs import sync_tables_daily_schedule, sync_tables_job

defs = dg.Definitions(
    assets=dg.load_assets_from_modules([assets]),
    jobs=[sync_tables_job],
    schedules=[sync_tables_daily_schedule],
)
""",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-elt-nested-definitions.py",
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

        create_file(
            Path("my_existing_project") / "definitions.py",
            """from pathlib import Path

import dagster_components as dg_components
from my_existing_project.analytics import assets as analytics_assets
from my_existing_project.analytics.jobs import (
    regenerate_analytics_hourly_schedule,
    regenerate_analytics_job,
)

import dagster as dg

defs = dg.Definitions.merge(
    dg.Definitions(
        assets=dg.load_assets_from_modules([analytics_assets]),
        jobs=[regenerate_analytics_job],
        schedules=[regenerate_analytics_hourly_schedule],
    ),
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

        # migrate analytics
        _run_command(
            cmd="dg component scaffold 'definitions@dagster_components' analytics-definitions",
        )
        _run_command(
            cmd="mv my_existing_project/analytics/* my_existing_project/components/analytics-definitions && rm -rf my_existing_project/analytics",
        )
        create_file(
            Path("my_existing_project")
            / "components"
            / "analytics-definitions"
            / "definitions.py",
            """import dagster as dg

from . import assets
from .jobs import regenerate_analytics_hourly_schedule, regenerate_analytics_job

defs = dg.Definitions(
    assets=dg.load_assets_from_modules([assets]),
    jobs=[regenerate_analytics_job],
    schedules=[regenerate_analytics_hourly_schedule],
)
""",
        )
        create_file(
            Path("my_existing_project")
            / "components"
            / "analytics-definitions"
            / "component.yaml",
            """type: definitions@dagster_components

params:
  definitions_path: definitions.py
""",
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(
            r"find . -type d -name my_existing_project.egg-info -exec rm -r {} \+"
        )
        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-tree-after-all.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        create_file(
            Path("my_existing_project") / "definitions.py",
            """from pathlib import Path

import dagster_components as dg_components

defs = dg_components.build_component_defs(Path(__file__).parent / "components")
""",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-definitions-after-all.py",
        )
