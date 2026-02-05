import os
import textwrap
from contextlib import ExitStack
from pathlib import Path

import pytest
from dagster_dg_core.utils import activate_venv
from dagster_shared.utils import environ

from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_DBT_PARSE,
    MASK_EDITABLE_DAGSTER,
    MASK_JAFFLE_PLATFORM,
    MASK_PLUGIN_CACHE_REBUILD,
    MASK_TMP_WORKSPACE,
    DgTestPackageManager,
    format_multiline,
    get_editable_install_cmd_for_dg,
    get_editable_install_cmd_for_project,
    make_letter_iterator,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    compare_tree_output,
    isolated_snippet_generation_environment,
    re_ignore_after,
    re_ignore_before,
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

# Mask BetaWarning messages from dagster-evidence
_MASK_BETA_WARNING = (r"/[^\n]*BetaWarning:[^\n]*\n[^\n]*\n", "")


@pytest.mark.parametrize("package_manager", ["pip", "uv"])
@pytest.mark.flaky(max_runs=2)
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
        context = stack.enter_context(
            isolated_snippet_generation_environment(
                should_update_snippets=update_snippets,
                snapshot_base_dir=COMPONENTS_SNIPPETS_DIR,
                global_snippet_replace_regexes=[
                    MASK_EDITABLE_DAGSTER,
                    MASK_JAFFLE_PLATFORM,
                    _MASK_USING_ENVIRONMENT_LOG_MESSAGE,
                    _MASK_EMPTY_WARNINGS,
                    _MASK_BETA_WARNING,
                    MASK_PLUGIN_CACHE_REBUILD,
                ],
                # For multi-parameter tests which share snippets, we don't want to clear the
                # snapshot dir before updating the snippets
                clear_snapshot_dir_before_update=False,
            )
        )
        # We need to use editable dagster in testing context
        stack.enter_context(environ({"DG_USE_EDITABLE_DAGSTER": "1"}))

        context.run_command_and_snippet_output(
            cmd="dg --help",
            snippet_path=f"{next_snip_no()}-help.txt",
        )

        # Scaffold project
        scaffold_project_snip_no = next_snip_no()
        get_letter = make_letter_iterator()
        get_scaffold_project_snip_name = lambda: (
            f"{scaffold_project_snip_no}-{get_letter()}-{package_manager}-scaffold.txt"
        )
        if package_manager == "uv":
            context.run_command_and_snippet_output(
                cmd="create-dagster project jaffle-platform",
                snippet_path=get_scaffold_project_snip_name(),
                snippet_replace_regex=[
                    (r"Using CPython.*?(?:\n(?!\n).*)*\n\n", "...venv creation...\n"),
                    # Kind of a hack, this appears after you enter "y" at the prompt, but when
                    # we simulate the input we don't get the newline we get in terminal so we
                    # slide it in here.
                    (r"Running `uv sync`\.\.\.", "\nRunning `uv sync`..."),
                ],
                input_str="y\n",
                ignore_output=True,
                print_cmd="uvx create-dagster@latest project jaffle-platform",
            )
            context.run_command_and_snippet_output(
                cmd="cd jaffle-platform && source .venv/bin/activate",
                snippet_path=get_scaffold_project_snip_name(),
                ignore_output=True,
            )
            # Activate the virtual environment after creating it-- executing the above `source
            # .venv/bin/activate` command does not actually activate the virtual environment
            # across subsequent command invocations in this test.
            stack.enter_context(activate_venv(".venv"))
        elif package_manager == "pip":
            for cmd, print_cmd in [
                ("mkdir jaffle-platform && cd jaffle-platform", None),
                ("python -m venv .venv", None),
                ("source .venv/bin/activate", None),
                (
                    get_editable_install_cmd_for_dg(package_manager),
                    f"{install_cmd} dagster-dg-cli",
                ),
            ]:
                context.run_command_and_snippet_output(
                    cmd=cmd,
                    snippet_path=get_scaffold_project_snip_name(),
                    ignore_output=True,
                    print_cmd=print_cmd,
                )

                # Activate the virtual environment after creating it-- see above comment
                if cmd.startswith("source"):
                    stack.enter_context(activate_venv(".venv"))

            context.run_command_and_snippet_output(
                cmd="create-dagster project .",
                snippet_path=get_scaffold_project_snip_name(),
                ignore_output=True,
            )
            context.run_command_and_snippet_output(
                cmd=get_editable_install_cmd_for_project(Path("."), package_manager),
                snippet_path=get_scaffold_project_snip_name(),
                print_cmd=f"{install_cmd} -e .",
                ignore_output=True,
            )

        # Validate scaffolded files
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        context.run_command_and_snippet_output(
            cmd="tree",
            snippet_path=f"{next_snip_no()}-{package_manager}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.run_command_and_snippet_output(
            cmd="dg list components",
            snippet_path=f"{next_snip_no()}-dg-list-components.txt",
        )

        context.run_command_and_snippet_output(
            cmd=f"{install_cmd} --editable {EDITABLE_DIR / 'dagster-sling'}",
            snippet_path=f"{next_snip_no()}-{package_manager}-add-sling.txt",
            print_cmd=f"{install_cmd} dagster-sling",
            ignore_output=True,
        )

        context.run_command_and_snippet_output(
            cmd="dg list components",
            snippet_path=f"{next_snip_no()}-dg-list-components.txt",
        )

        # Scaffold new ingestion, validate new files
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs 'dagster_sling.SlingReplicationCollectionComponent' ingest_files",
            snippet_path=f"{next_snip_no()}-dg-scaffold-sling-replication.txt",
            # TODO turn output back on when we figure out how to handle multiple
            # "Using ..." messages from multiple dagster-components calls under the hood (when
            # cache disabled for pip)
            ignore_output=True,
        )

        # Cleanup __pycache__ directories
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        context.run_command_and_snippet_output(
            cmd="tree src/jaffle_platform",
            snippet_path=f"{next_snip_no()}-tree-jaffle-platform.txt",
            custom_comparison_fn=compare_tree_output,
        )

        ingest_files_defs_yaml_path = (
            Path("src") / "jaffle_platform" / "defs" / "ingest_files" / "defs.yaml"
        )

        context.check_file(
            ingest_files_defs_yaml_path,
            f"{next_snip_no()}-defs.yaml",
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
            context.run_command_and_snippet_output(
                cmd=textwrap.dedent("""
                    curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv &&
                    curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv &&
                    curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv
                """).strip(),
                snippet_path=f"{next_snip_no()}-curl.txt",
                ignore_output=True,
            )

            context.run_command_and_snippet_output(
                cmd=f"{install_cmd} duckdb",
                snippet_path=f"{next_snip_no()}-{package_manager}-add-duckdb.txt",
                print_cmd=f"{install_cmd} duckdb",
                ignore_output=True,
            )

            context.create_file(
                file_path=Path("src")
                / "jaffle_platform"
                / "defs"
                / "ingest_files"
                / "replication.yaml",
                snippet_path=f"{next_snip_no()}-replication.yaml",
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
            context.create_file(
                ingest_files_defs_yaml_path,
                snippet_path=f"{next_snip_no()}-component-connections.yaml",
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

            _run_command("dg launch --assets '*'")
            context.run_command_and_snippet_output(
                cmd='duckdb /tmp/jaffle_platform.duckdb -c "SELECT * FROM raw_customers LIMIT 5;"',
                snippet_path=f"{next_snip_no()}-duckdb-select.txt",
                snippet_replace_regex=[
                    (r"\d\d\d\d\d\d\d\d\d\d │\n", "...        | \n"),
                ],
            )

            # Set up dbt
            context.run_command_and_snippet_output(
                cmd="git clone --depth=1 https://github.com/dagster-io/jaffle-platform.git dbt && rm -rf dbt/.git",
                snippet_path=f"{next_snip_no()}-jaffle-clone.txt",
                ignore_output=True,
            )
            context.run_command_and_snippet_output(
                cmd=f"{install_cmd} --editable {EDITABLE_DIR / 'dagster-dbt'} && {install_cmd} dbt-duckdb",
                snippet_path=f"{next_snip_no()}-{package_manager}-add-dbt.txt",
                print_cmd=f"{install_cmd} dagster-dbt dbt-duckdb",
                ignore_output=True,
            )
            context.run_command_and_snippet_output(
                cmd="dg list components",
                snippet_path=f"{next_snip_no()}-dg-list-components.txt",
            )

            # Scaffold dbt project components
            context.run_command_and_snippet_output(
                cmd="dg scaffold defs dagster_dbt.DbtProjectComponent jdbt --project-path dbt/jdbt",
                snippet_path=f"{next_snip_no()}-dg-scaffold-jdbt.txt",
                # TODO turn output back on when we figure out how to handle multiple
                # "Using ..." messages from multiple dagster-components calls under the hood
                # (when cache disabled for pip)
                ignore_output=True,
            )
            context.check_file(
                Path("src") / "jaffle_platform" / "defs" / "jdbt" / "defs.yaml",
                COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-component-jdbt.yaml",
            )

            # Update component file, with error, check and fix
            context.create_file(
                Path("src") / "jaffle_platform" / "defs" / "jdbt" / "defs.yaml",
                snippet_path=f"{next_snip_no()}-project-jdbt-incorrect.yaml",
                contents=format_multiline("""
                    type: dagster_dt.dbt_project

                    attributes:
                      project: "{{ project_root }}/dbt/jdbt"
                      translation:
                        key: "target/main/{{ node.name }}
                """),
            )
            context.run_command_and_snippet_output(
                cmd="dg check yaml",
                snippet_path=f"{next_snip_no()}-dg-component-check-error.txt",
                expect_error=True,
            )

            context.create_file(
                Path("src") / "jaffle_platform" / "defs" / "jdbt" / "defs.yaml",
                snippet_path=f"{next_snip_no()}-project-jdbt.yaml",
                contents=format_multiline("""
                    type: dagster_dbt.DbtProjectComponent

                    attributes:
                      project: "{{ project_root }}/dbt/jdbt"
                      translation:
                        key: "target/main/{{ node.name }}"
                """),
            )
            context.run_command_and_snippet_output(
                cmd="dg check yaml",
                snippet_path=f"{next_snip_no()}-dg-component-check.txt",
            )

            # Run dbt, check works
            if not update_snippets:
                _run_command("dg launch --assets '*'")
            context.run_command_and_snippet_output(
                cmd='duckdb /tmp/jaffle_platform.duckdb -c "SELECT * FROM orders LIMIT 5;"',
                snippet_path=f"{next_snip_no()}-duckdb-select-orders.txt",
            )

            # Evidence.dev

            context.run_command_and_snippet_output(
                cmd=f"{install_cmd} dagster-evidence",
                snippet_path=f"{next_snip_no()}-{package_manager}-add-evidence.txt",
                ignore_output=True,
            )

            context.run_command_and_snippet_output(
                cmd="dg list components",
                snippet_path=f"{next_snip_no()}-dg-list-components.txt",
            )

            context.run_command_and_snippet_output(
                cmd="git clone --depth=1 https://github.com/dagster-io/jaffle-dashboard.git jaffle_dashboard && rm -rf jaffle_dashboard/.git",
                snippet_path=f"{next_snip_no()}-jaffle-dashboard-clone.txt",
                ignore_output=True,
            )

            context.run_command_and_snippet_output(
                cmd="dg scaffold defs dagster_evidence.EvidenceProject jaffle_dashboard",
                snippet_path=f"{next_snip_no()}-scaffold-jaffle-dashboard.txt",
                # TODO turn output back on when we figure out how to handle multiple
                # "Using ..." messages from multiple dagster-components calls under the hood
                # (when cache disabled for pip)
                ignore_output=True,
            )

            context.check_file(
                Path("src")
                / "jaffle_platform"
                / "defs"
                / "jaffle_dashboard"
                / "defs.yaml",
                COMPONENTS_SNIPPETS_DIR
                / f"{next_snip_no()}-component-jaffle-dashboard.yaml",
            )

            context.create_file(
                Path("src")
                / "jaffle_platform"
                / "defs"
                / "jaffle_dashboard"
                / "defs.yaml",
                snippet_path=f"{next_snip_no()}-project-jaffle-dashboard.yaml",
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
            context.run_command_and_snippet_output(
                cmd="dg check yaml",
                snippet_path=f"{next_snip_no()}-dg-component-check-yaml.txt",
            )

            context.run_command_and_snippet_output(
                cmd="dg check defs",
                snippet_path=f"{next_snip_no()}-dg-component-check-defs.txt",
                snippet_replace_regex=[
                    MASK_TMP_WORKSPACE,
                    MASK_DBT_PARSE,
                ],
            )

            # Schedule
            context.run_command_and_snippet_output(
                cmd="dg scaffold defs dagster.schedule daily_jaffle.py",
                snippet_path=f"{next_snip_no()}-scaffold-daily-jaffle.txt",
                # TODO turn output back on when we figure out how to handle multiple
                # "Using ..." messages from multiple dagster-components calls under the hood (when
                # cache disabled for pip)
                ignore_output=True,
            )

            context.create_file(
                Path("src") / "jaffle_platform" / "defs" / "daily_jaffle.py",
                snippet_path=f"{next_snip_no()}-daily-jaffle.py",
                contents=format_multiline("""
                    import dagster as dg


                    @dg.schedule(cron_schedule="@daily", target="*")
                    def daily_jaffle(context: dg.ScheduleEvaluationContext):
                        return dg.RunRequest()
                """),
            )

            if not update_snippets:
                _run_command("dg launch --assets '* and not key:jaffle_dashboard'")
