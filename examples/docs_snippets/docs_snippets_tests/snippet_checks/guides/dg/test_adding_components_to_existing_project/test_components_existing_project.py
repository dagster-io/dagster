import textwrap
from pathlib import Path

from dagster_dg_core.utils import activate_venv

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    format_multiline,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    compare_tree_output,
    isolated_snippet_generation_environment,
)

MASK_MY_EXISTING_PROJECT = (r" \/.*?\/my-existing-project", " /.../my-existing-project")
MASK_ISORT = (r"#isort:skip-file", "# definitions.py")
MASK_VENV = (r"Using.*\.venv.*", "")
MASK_USING_LOG_MESSAGE = (r"Using.*\n", "")
MASK_PKG_RESOURCES = (r"\n.*import pkg_resources\n", "")


SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "dg"
    / "adding-components-to-existing-project"
)


MY_EXISTING_PROJECT = Path(__file__).parent / "my-existing-project"


def test_components_existing_project(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment(
        should_update_snippets=update_snippets,
        snapshot_base_dir=SNIPPETS_DIR,
        global_snippet_replace_regexes=[MASK_PKG_RESOURCES],
    ) as context:
        _run_command(f"cp -r {MY_EXISTING_PROJECT} . && cd my-existing-project")
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(
            r"find . -type d -name my_existing_project.egg-info -exec rm -r {} \+"
        )

        context.run_command_and_snippet_output(
            cmd="tree",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("my_existing_project") / "definitions.py",
            SNIPPETS_DIR / f"{context.get_next_snip_number()}-definitions-before.py",
            snippet_replace_regex=[MASK_ISORT],
        )

        _run_command(cmd="uv venv")
        _run_command(
            f"uv add --editable '{DAGSTER_ROOT / 'python_modules' / 'dagster'!s}' "
            f"'{DAGSTER_ROOT / 'python_modules' / 'libraries' / 'dagster-shared'!s}' "
            f"'{DAGSTER_ROOT / 'python_modules' / 'dagster-webserver'!s}' "
            f"'{DAGSTER_ROOT / 'python_modules' / 'dagster-pipes'!s}' "
            f"'{DAGSTER_ROOT / 'python_modules' / 'dagster-graphql'!s}' "
            f"'{DAGSTER_ROOT / 'python_modules' / 'libraries' / 'dagster-sling'!s}'"
        )

        context.run_command_and_snippet_output(
            cmd=textwrap.dedent(
                """
                    curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv
                """
            ).strip(),
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-curl.txt",
            ignore_output=True,
        )

        context.run_command_and_snippet_output(
            cmd="mkdir -p my_existing_project/elt/sling",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-mkdir.txt",
        )

        context.create_file(
            file_path=Path("my_existing_project")
            / "elt"
            / "sling"
            / "replication.yaml",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-replication.yaml",
            contents=textwrap.dedent(
                """
                        source: LOCAL
                        target: DUCKDB

                        defaults:
                          mode: full-refresh
                          object: "{stream_table}"

                        streams:
                          file://raw_customers.csv:
                            object: "sandbox.raw_customers"
                    """,
            ).strip(),
        )

        # update definitions.py
        context.create_file(
            file_path=Path("my_existing_project") / "definitions.py",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-definitions.py",
            contents=textwrap.dedent(
                """
                    from pathlib import Path

                    import dagster_sling
                    from dagster_sling import (
                        SlingConnectionResource,
                        SlingReplicationCollectionComponent,
                        SlingReplicationSpecModel,
                    )
                    from my_existing_project.analytics import assets as analytics_assets
                    from my_existing_project.analytics.jobs import (
                        regenerate_analytics_hourly_schedule,
                        regenerate_analytics_job,
                    )
                    from my_existing_project.elt import assets as elt_assets
                    from my_existing_project.elt.jobs import sync_tables_daily_schedule, sync_tables_job

                    import dagster as dg

                    defs = dg.Definitions.merge(
                        dg.Definitions(
                            assets=dg.load_assets_from_modules([elt_assets, analytics_assets]),
                            jobs=[sync_tables_job, regenerate_analytics_job],
                            schedules=[sync_tables_daily_schedule, regenerate_analytics_hourly_schedule],
                        ),
                        dg.build_defs_for_component(
                            component=SlingReplicationCollectionComponent(
                                connections=[
                                    SlingConnectionResource(
                                        name="DUCKDB",
                                        type="duckdb",
                                        instance="/tmp/jaffle_platform.duckdb",
                                    )
                                ],
                                replications=[
                                    SlingReplicationSpecModel(
                                        path=(
                                            Path(__file__).parent / "elt" / "sling" / "replication.yaml"
                                        ).as_posix(),
                                    )
                                ],
                            )
                        ),
                    )
                """
            ).strip(),
        )

        # ensure the component is loaded
        if not update_snippets:
            _run_command(
                "uv pip freeze && uv run dagster asset materialize --select '*' -m 'my_existing_project.definitions'"
            )
