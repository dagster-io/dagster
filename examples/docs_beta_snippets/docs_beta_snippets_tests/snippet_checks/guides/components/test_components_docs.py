import os
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from dagster._utils.env import environ
from docs_beta_snippets_tests.snippet_checks.utils import (
    _run_command,
    check_file,
    create_file,
    re_ignore_after,
    re_ignore_before,
    run_command_and_snippet_output,
)

MASK_TIME = (r"\d+:\d+(:?AM|PM)", "9:00AM")
MASK_SLING_WARNING = (r"warning.*\n", "")
MASK_SLING_PROMO = (r"Follow Sling.*\n", "")
MASK_JAFFLE_PLATFORM = (r" \/.*?\/jaffle-platform", " /.../jaffle-platform")

DAGSTER_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_beta_snippets"
    / "docs_beta_snippets"
    / "guides"
    / "components"
    / "index"
)


def test_components_docs_index(update_snippets: bool) -> None:
    snip_no = 0

    def next_snip_no():
        nonlocal snip_no
        snip_no += 1
        return snip_no

    with TemporaryDirectory() as tempdir, environ({"COLUMNS": "80", "NO_COLOR": "1"}):
        os.chdir(tempdir)
        subprocess.check_call(["uv", "pip", "install", "dg"])

        run_command_and_snippet_output(
            cmd="dg --help",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-help.txt",
            update_snippets=update_snippets,
        )

        # Scaffold code location
        run_command_and_snippet_output(
            cmd="dg code-location scaffold jaffle-platform",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-scaffold.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_JAFFLE_PLATFORM,
                (r"\nUsing[\s\S]*", "\n..."),
            ],
        )

        # Validate scaffolded files
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        run_command_and_snippet_output(
            cmd="cd jaffle-platform && tree",
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
        check_file(
            Path("jaffle_platform") / "definitions.py",
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
                    '"dagster.components" = { jaffle_platform = "jaffle_platform.lib"}'
                ),
            ],
        )

        run_command_and_snippet_output(
            cmd="dg component-type list",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-list-component-types.txt",
            update_snippets=update_snippets,
        )
        components_dir = str(
            DAGSTER_ROOT / "python_modules" / "libraries" / "dagster-components"
        )
        _run_command(f"uv add --editable '{components_dir}[sling]'")
        run_command_and_snippet_output(
            cmd="dg component-type list",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-list-component-types.txt",
            update_snippets=update_snippets,
        )

        # Scaffold new ingestion, validate new files
        run_command_and_snippet_output(
            cmd="dg component scaffold dagster_components.sling_replication_collection ingest_files",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-scaffold-sling-replication.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_JAFFLE_PLATFORM],
        )
        # Cleanup __pycache__ directories
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        run_command_and_snippet_output(
            cmd="tree jaffle_platform",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-tree-jaffle-platform.txt",
            update_snippets=update_snippets,
        )
        check_file(
            Path("jaffle_platform") / "components" / "ingest_files" / "component.yaml",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-component.yaml",
            update_snippets=update_snippets,
        )

        # Set up duckdb Sling connection
        run_command_and_snippet_output(
            cmd="uv run sling conns set DUCKDB type=duckdb instance=/tmp/jaffle_platform.duckdb",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-sling-setup-duckdb.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_SLING_WARNING,
                MASK_SLING_PROMO,
                MASK_TIME,
                (r"/Users/.*?/.sling", "/.../.sling"),
            ],
        )
        run_command_and_snippet_output(
            cmd="uv run sling conns test DUCKDB",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-sling-test-duckdb.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_SLING_WARNING, MASK_SLING_PROMO, MASK_TIME],
        )

        # Test sling sync
        run_command_and_snippet_output(
            cmd="""curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv &&
curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv &&
curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv""",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-curl.txt",
            update_snippets=update_snippets,
            ignore_output=True,
        )
        create_file(
            file_path=Path("jaffle_platform")
            / "components"
            / "ingest_files"
            / "replication.yaml",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-replication.yaml",
            contents="""
### jaffle_platform/components/ingest_files/replication.yaml

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
        )
        _run_command(
            "dagster asset materialize --select '*' -m jaffle_platform.definitions"
        )
        run_command_and_snippet_output(
            cmd='duckdb /tmp/jaffle_platform.duckdb -c "SELECT * FROM raw_customers LIMIT 5;"',
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-duckdb-select.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[(r"\d\d\d\d\d\d\d\d\d\d │\n", "...        | \n")],
        )

        # Set up dbt
        run_command_and_snippet_output(
            cmd="git clone --depth=1 https://github.com/dagster-io/jaffle-platform.git dbt && rm -rf dbt/.git",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-jaffle-clone.txt",
            update_snippets=update_snippets,
            ignore_output=True,
        )
        _run_command(f"uv add --editable '{components_dir}[dbt]'; uv add dbt-duckdb")
        run_command_and_snippet_output(
            cmd="dg component-type list",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-list-component-types.txt",
            update_snippets=update_snippets,
        )
        run_command_and_snippet_output(
            cmd="dg component-type info dagster_components.dbt_project",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-component-type-info.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[re_ignore_after("Component params schema:")],
        )

        # Scaffold dbt project components
        run_command_and_snippet_output(
            cmd="dg component scaffold dagster_components.dbt_project jdbt --project-path dbt/jdbt",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-dg-scaffold-jdbt.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_JAFFLE_PLATFORM],
        )
        check_file(
            Path("jaffle_platform") / "components" / "jdbt" / "component.yaml",
            COMPONENTS_SNIPPETS_DIR / f"{next_snip_no()}-component-jdbt.yaml",
            update_snippets=update_snippets,
        )
        create_file(
            Path("jaffle_platform") / "components" / "jdbt" / "component.yaml",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{next_snip_no()}-project-jdbt.yaml",
            contents="""type: dagster_components.dbt_project

params:
  dbt:
    project_dir: ../../../dbt/jdbt
  asset_attributes:
    key: "target/main/{{ node.name }}"
""",
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
