import os
import textwrap
from contextlib import ExitStack
from pathlib import Path
from typing import Literal, Optional

import pytest
from dagster_dg.cli.utils import activate_venv, environ
from typing_extensions import TypeAlias

from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_EDITABLE_DAGSTER,
    MASK_JAFFLE_PLATFORM,
    MASK_PLUGIN_CACHE_REBUILD,
    MASK_TMP_WORKSPACE,
    DgTestPackageManager,
    format_multiline,
    get_editable_install_cmd_for_dg,
    get_editable_install_cmd_for_project,
    isolated_snippet_generation_environment,
    make_letter_iterator,
)
from docs_snippets_tests.snippet_checks.utils import (
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
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "components"
    / "index"
)

_MASK_USING_ENVIRONMENT_LOG_MESSAGE = (r"\nUsing \S*\n", "\n")

# For some reason dagster-evidence is producing this in the output:
#
#    <blank line>
#        warnings.warn(message)
#
# Mask this until we figure out how to get rid of it.
_MASK_EMPTY_WARNINGS = (r"\n +warnings.warn\(message\)\n", "")


@pytest.mark.parametrize("package_manager", ["pip", "uv"])
def test_components_docs_index(
    package_manager: DgTestPackageManager, update_snippets: bool
) -> None:
    if package_manager == "uv":
        install_cmd = "uv add"
    elif package_manager == "pip":
        install_cmd = "pip install"

    snip_no = 0

    def next_snip_no() -> int:
        nonlocal snip_no
        snip_no += 1
        return snip_no

    with ExitStack() as stack:
        stack.enter_context(isolated_snippet_generation_environment())
        # We need to use editable dagster in testing context
        stack.enter_context(environ({"DG_USE_EDITABLE_DAGSTER": "1"}))
        run_command_and_snippet_output(
            cmd="dg --help",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-help.txt",
            update_snippets=update_snippets,
        )

        # Scaffold project
        scaffold_project_snip_no = next_snip_no()
        get_letter = make_letter_iterator()
        get_scaffold_project_snip_name = (
            lambda: f"{scaffold_project_snip_no}-{get_letter()}-{package_manager}-scaffold.txt"
        )
        if package_manager == "uv":
            run_command_and_snippet_output(
                cmd="dg scaffold project jaffle-platform",
                snippet_path=COMPONENTS_SNIPPETS_DIR / get_scaffold_project_snip_name(),
                update_snippets=update_snippets,
                snippet_replace_regex=[
                    MASK_EDITABLE_DAGSTER,
                    MASK_JAFFLE_PLATFORM,
                    (r"Using CPython.*?(?:\n(?!\n).*)*\n\n", "...venv creation...\n"),
                    # Kind of a hack, this appears after you enter "y" at the prompt, but when
                    # we simulate the input we don't get the newline we get in terminal so we
                    # slide it in here.
                    (r"Running `uv sync`\.\.\.", "\nRunning `uv sync`..."),
                ],
                input_str="y\n",
                ignore_output=True,
            )
            run_command_and_snippet_output(
                cmd="cd jaffle-platform && source .venv/bin/activate",
                snippet_path=COMPONENTS_SNIPPETS_DIR / get_scaffold_project_snip_name(),
                update_snippets=update_snippets,
                ignore_output=True,
            )
            # Activate the virtual environment after creating it-- executing the above `source
            # .venv/bin/activate` command does not actually activate the virtual environment
            # across subsequent command invocations in this test.
            stack.enter_context(activate_venv(".venv"))
        elif package_manager == "pip":
            dagster_dg_path = EDITABLE_DIR / "dagster-dg"
            dagster_shared_path = EDITABLE_DIR / "dagster-shared"
            for cmd, print_cmd in [
                ("mkdir jaffle-platform && cd jaffle-platform", None),
                ("python -m venv .venv", None),
                ("source .venv/bin/activate", None),
                (
                    get_editable_install_cmd_for_dg(package_manager),
                    f"{install_cmd} dagster-dg",
                ),
            ]:
                run_command_and_snippet_output(
                    cmd=cmd,
                    snippet_path=COMPONENTS_SNIPPETS_DIR
                    / get_scaffold_project_snip_name(),
                    update_snippets=update_snippets,
                    ignore_output=True,
                    print_cmd=print_cmd,
                    snippet_replace_regex=[
                        MASK_JAFFLE_PLATFORM,
                    ],
                )

                # Activate the virtual environment after creating it-- see above comment
                if cmd.startswith("source"):
                    stack.enter_context(activate_venv(".venv"))

            run_command_and_snippet_output(
                cmd="dg scaffold project .",
                snippet_path=COMPONENTS_SNIPPETS_DIR / get_scaffold_project_snip_name(),
                update_snippets=update_snippets,
                snippet_replace_regex=[
                    MASK_EDITABLE_DAGSTER,
                    MASK_JAFFLE_PLATFORM,
                    _MASK_USING_ENVIRONMENT_LOG_MESSAGE,
                ],
                ignore_output=True,
            )
            run_command_and_snippet_output(
                cmd=get_editable_install_cmd_for_project(Path("."), package_manager),
                snippet_path=COMPONENTS_SNIPPETS_DIR / get_scaffold_project_snip_name(),
                update_snippets=update_snippets,
                print_cmd=f"{install_cmd} -e .",
                ignore_output=True,
            )

        # Validate scaffolded files
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-{package_manager}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )
        check_file(
            "pyproject.toml",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-pyproject.toml",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                re_ignore_before("[tool.dg]"),
                re_ignore_after('root_module = "jaffle_platform"'),
            ],
        )
        check_file(
            Path("src") / "jaffle_platform" / "definitions.py",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-definitions.py",
            update_snippets=update_snippets,
        )
        check_file(
            "pyproject.toml",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-pyproject.toml",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                re_ignore_before("[project.entry-points]"),
                re_ignore_after(
                    '"dagster_dg.plugin" = { jaffle_platform = "jaffle_platform.components"}'
                ),
            ],
        )

        run_command_and_snippet_output(
            cmd="dg list plugins",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-list-plugins.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_JAFFLE_PLATFORM,
                MASK_PLUGIN_CACHE_REBUILD,
                _MASK_EMPTY_WARNINGS,
            ],
        )

        run_command_and_snippet_output(
            cmd=f"{install_cmd} --editable {EDITABLE_DIR / 'dagster-sling'}",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-{package_manager}-add-sling.txt",
            update_snippets=update_snippets,
            print_cmd=f"{install_cmd} dagster-sling",
            ignore_output=True,
        )

        run_command_and_snippet_output(
            cmd="dg list plugins",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-list-plugins.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_JAFFLE_PLATFORM,
                MASK_PLUGIN_CACHE_REBUILD,
                _MASK_EMPTY_WARNINGS,
            ],
        )

        # Scaffold new ingestion, validate new files
        run_command_and_snippet_output(
            cmd="dg scaffold 'dagster_sling.SlingReplicationCollectionComponent' ingest_files",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-scaffold-sling-replication.txt",
            update_snippets=update_snippets,
            # TODO turn output back on when we figure out how to handle multiple
            # "Using ..." messages from multiple dagster-components calls under the hood (when
            # cache disabled for pip)
            ignore_output=True,
        )

        # Cleanup __pycache__ directories
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        run_command_and_snippet_output(
            cmd="tree src/jaffle_platform",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-tree-jaffle-platform.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        ingest_files_component_yaml_path = (
            Path("src") / "jaffle_platform" / "defs" / "ingest_files" / "component.yaml"
        )

        check_file(
            ingest_files_component_yaml_path,
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-component.yaml",
            update_snippets=update_snippets,
        )

        sling_duckdb_path = Path("/") / "tmp" / ".sling" / "bin" / "duckdb"
        sling_duckdb_version = next(iter(os.listdir()), None)
        with environ(
            {
                "PATH": f"{os.environ['PATH']}:{sling_duckdb_path / sling_duckdb_version!s}"
            }
            if sling_duckdb_version
            else {}
        ):
            run_command_and_snippet_output(
                cmd=textwrap.dedent("""
                    curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv &&
                    curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv &&
                    curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv
                """).strip(),
                snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-curl.txt",
                update_snippets=update_snippets,
                ignore_output=True,
            )

            create_file(
                file_path=Path("src")
                / "jaffle_platform"
                / "defs"
                / "ingest_files"
                / "replication.yaml",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-replication.yaml",
                contents=textwrap.dedent(
                    """
                    source: LOCAL
                    target: DUCKDB

                    defaults:
                      mode: full-refresh
                      object: "{stream_table}"

                    streams:
                      file://raw_customers.csv:
                        object: "main.raw_customers"
                      file://raw_orders.csv:
                        object: "main.raw_orders"
                      file://raw_payments.csv:
                        object: "main.raw_payments"
                """,
                ).strip(),
            )

            # Add duckdb connection
            create_file(
                ingest_files_component_yaml_path,
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-component-connections.yaml",
                contents=format_multiline("""
                    type: dagster_sling.SlingReplicationCollectionComponent

                    attributes:
                      sling:
                        connections:
                          - name: DUCKDB
                            type: duckdb
                            instance: /tmp/jaffle_platform.duckdb
                      replications:
                        - path: replication.yaml
                    """),
            )

            # Test sling sync

            _run_command(
                "dagster asset materialize --select '*' -m jaffle_platform.definitions"
            )
            run_command_and_snippet_output(
                cmd='duckdb /tmp/jaffle_platform.duckdb -c "SELECT * FROM raw_customers LIMIT 5;"',
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-duckdb-select.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[
                    (r"\d\d\d\d\d\d\d\d\d\d │\n", "...        | \n"),
                ],
            )

            # Set up dbt
            run_command_and_snippet_output(
                cmd="git clone --depth=1 https://github.com/dagster-io/jaffle-platform.git dbt && rm -rf dbt/.git",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-jaffle-clone.txt",
                update_snippets=update_snippets,
                ignore_output=True,
            )
            run_command_and_snippet_output(
                cmd=f"{install_cmd} --editable {EDITABLE_DIR / 'dagster-dbt'} && {install_cmd} dbt-duckdb",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-{package_manager}-add-dbt.txt",
                update_snippets=update_snippets,
                print_cmd=f"{install_cmd} dagster-dbt dbt-duckdb",
                ignore_output=True,
            )
            run_command_and_snippet_output(
                cmd="dg list plugins",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-dg-list-plugins.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[
                    MASK_JAFFLE_PLATFORM,
                    MASK_PLUGIN_CACHE_REBUILD,
                    _MASK_EMPTY_WARNINGS,
                ],
            )

            # Scaffold dbt project components
            run_command_and_snippet_output(
                cmd="dg scaffold dagster_dbt.DbtProjectComponent jdbt --project-path dbt/jdbt",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-dg-scaffold-jdbt.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[MASK_JAFFLE_PLATFORM],
                # TODO turn output back on when we figure out how to handle multiple
                # "Using ..." messages from multiple dagster-components calls under the hood
                # (when cache disabled for pip)
                ignore_output=True,
            )
            check_file(
                Path("src") / "jaffle_platform" / "defs" / "jdbt" / "component.yaml",
                COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-component-jdbt.yaml",
                update_snippets=update_snippets,
            )

            # Update component file, with error, check and fix
            create_file(
                Path("src") / "jaffle_platform" / "defs" / "jdbt" / "component.yaml",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-project-jdbt-incorrect.yaml",
                contents=format_multiline("""
                    type: dagster_dt.dbt_project

                    attributes:
                      project: "{{ project_root }}/dbt/jdbt"
                      translation:
                        key: "target/main/{{ node.name }}
                """),
            )
            run_command_and_snippet_output(
                cmd="dg check yaml",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-dg-component-check-error.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[
                    _MASK_USING_ENVIRONMENT_LOG_MESSAGE,  # TODO: Remove when caching implemented for pip
                    _MASK_EMPTY_WARNINGS,  # TODO: Remove when caching implemented for pip
                    MASK_JAFFLE_PLATFORM,
                ],
                expect_error=True,
            )

            create_file(
                Path("src") / "jaffle_platform" / "defs" / "jdbt" / "component.yaml",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-project-jdbt.yaml",
                contents=format_multiline("""
                    type: dagster_dbt.DbtProjectComponent

                    attributes:
                      project: "{{ project_root }}/dbt/jdbt"
                      translation:
                        key: "target/main/{{ node.name }}"
                """),
            )
            run_command_and_snippet_output(
                cmd="dg check yaml",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-dg-component-check.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[
                    _MASK_USING_ENVIRONMENT_LOG_MESSAGE,  # TODO: Remove when caching implemented for pip
                    _MASK_EMPTY_WARNINGS,
                    MASK_JAFFLE_PLATFORM,
                ],
            )

            # Run dbt, check works
            _run_command(
                "DAGSTER_IS_DEV_CLI=1 dagster asset materialize --select '*' -m jaffle_platform.definitions"
            )
            run_command_and_snippet_output(
                cmd='duckdb /tmp/jaffle_platform.duckdb -c "SELECT * FROM orders LIMIT 5;"',
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-duckdb-select-orders.txt",
                update_snippets=update_snippets,
            )

            # Evidence.dev

            run_command_and_snippet_output(
                cmd=f"{install_cmd} dagster-evidence",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-{package_manager}-add-evidence.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[MASK_JAFFLE_PLATFORM],
                ignore_output=True,
            )

            run_command_and_snippet_output(
                cmd="dg list plugins",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-dg-list-plugins.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[
                    MASK_JAFFLE_PLATFORM,
                    MASK_PLUGIN_CACHE_REBUILD,
                    _MASK_EMPTY_WARNINGS,
                ],
            )

            run_command_and_snippet_output(
                cmd="git clone --depth=1 https://github.com/dagster-io/jaffle-dashboard.git jaffle_dashboard && rm -rf jaffle_dashboard/.git",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-jaffle-dashboard-clone.txt",
                update_snippets=update_snippets,
                ignore_output=True,
            )

            run_command_and_snippet_output(
                cmd="dg scaffold dagster_evidence.EvidenceProject jaffle_dashboard",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-scaffold-jaffle-dashboard.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[MASK_JAFFLE_PLATFORM],
                # TODO turn output back on when we figure out how to handle multiple
                # "Using ..." messages from multiple dagster-components calls under the hood
                # (when cache disabled for pip)
                ignore_output=True,
            )

            check_file(
                Path("src")
                / "jaffle_platform"
                / "defs"
                / "jaffle_dashboard"
                / "component.yaml",
                COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-component-jaffle-dashboard.yaml",
                update_snippets=update_snippets,
            )

            create_file(
                Path("src")
                / "jaffle_platform"
                / "defs"
                / "jaffle_dashboard"
                / "component.yaml",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-project-jaffle-dashboard.yaml",
                contents=format_multiline("""
                    type: dagster_evidence.EvidenceProject

                    attributes:
                      project_path: ../../../../jaffle_dashboard
                      asset:
                        key: jaffle_dashboard
                        deps:
                          - target/main/orders
                          - target/main/customers
                      deploy_command: 'echo "Dashboard built at $EVIDENCE_BUILD_PATH"'
                """),
            )
            run_command_and_snippet_output(
                cmd="dg check yaml",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-dg-component-check-yaml.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[
                    _MASK_USING_ENVIRONMENT_LOG_MESSAGE,  # TODO: Remove when caching implemented for pip
                    MASK_JAFFLE_PLATFORM,
                    _MASK_EMPTY_WARNINGS,
                ],
            )

            run_command_and_snippet_output(
                cmd="dg check defs",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-dg-component-check-defs.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[
                    _MASK_USING_ENVIRONMENT_LOG_MESSAGE,  # TODO: Remove when caching implemented for pip
                    MASK_JAFFLE_PLATFORM,
                    MASK_TMP_WORKSPACE,
                    _MASK_EMPTY_WARNINGS,
                ],
            )

            # Schedule
            run_command_and_snippet_output(
                cmd="dg scaffold dagster.schedule daily_jaffle.py",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-scaffold-daily-jaffle.txt",
                update_snippets=update_snippets,
                snippet_replace_regex=[
                    MASK_JAFFLE_PLATFORM,
                    _MASK_EMPTY_WARNINGS,
                ],
                # TODO turn output back on when we figure out how to handle multiple
                # "Using ..." messages from multiple dagster-components calls under the hood (when
                # cache disabled for pip)
                ignore_output=True,
            )

            create_file(
                Path("src") / "jaffle_platform" / "defs" / "daily_jaffle.py",
                snippet_path=COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-daily-jaffle.py",
                contents=format_multiline("""
                    import dagster as dg


                    @dg.schedule(cron_schedule="@daily", target="*")
                    def daily_jaffle(context: dg.ScheduleEvaluationContext):
                        return dg.RunRequest()
                """),
            )

            _run_command(
                "DAGSTER_IS_DEV_CLI=1 dagster asset materialize --select '* and not key:jaffle_dashboard' -m jaffle_platform.definitions"
            )
