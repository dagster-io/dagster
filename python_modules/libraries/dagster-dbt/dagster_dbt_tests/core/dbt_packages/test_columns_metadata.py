import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from _pytest.mark.structures import ParameterSet
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSelection,
    AssetSpec,
    TableColumn,
    TableColumnDep,
    TableColumnLineage,
    TableSchema,
    _check as check,
    materialize,
)
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.definitions.metadata.table import TableColumnConstraints
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core import dbt_cli_event
from dagster_dbt.core.dbt_cli_event import _get_compiled_sql
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.dbt_project import DbtProject
from pytest_mock import MockFixture
from sqlglot import Dialect

from dagster_dbt_tests.conftest import _create_dbt_invocation
from dagster_dbt_tests.dbt_projects import (
    test_dbt_snapshot_column_lineage_path,
    test_dependencies_path,
    test_jaffle_shop_path,
    test_metadata_path,
)

pytestmark: pytest.MarkDecorator = pytest.mark.derived_metadata


@pytest.fixture(autouse=True)
def _isolated_duckdb_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Give each test its own DuckDB database file in a pytest tmp_path.

    These tests use ``fetch_column_metadata``, which opens an in-process READ_ONLY
    DuckDB adapter connection via ``dbt.adapters.factory``. The adapter registry is a
    process-global singleton, so a connection opened in one test can linger into the
    next test's ``dbt build`` subprocess and cause ``IO Error: Could not set lock on
    file`` failures. Giving each test its own DB file eliminates the shared resource
    entirely — no lock conflict is possible regardless of adapter cleanup timing.

    The filename stem is preserved from the session-scoped fixture in ``conftest.py``:
    in DuckDB the database identifier is derived from the file stem, and the
    session-scoped ``test_metadata_manifest`` fixture builds the project (including
    dbt's partial-parse cache at ``target/partial_parse.msgpack``) with SQL that
    qualifies tables as ``{stem}.main.<table>``. Changing the stem would leave the
    compiled references dangling.

    The session-built DB file is copied into tmp_path when present. The
    ``source_raw_customers`` table (created by ``init_db.py`` at session setup) must
    exist before ``stg_customers.sql`` can be built — copying the session DB
    preserves it. ``tmp_path`` is cleaned up by pytest, so this adds no persistent
    disk footprint.
    """
    db_file_name = os.environ["DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_NAME"]
    db_path = tmp_path / f"{db_file_name}.duckdb"

    # The session-scoped ``test_metadata_manifest`` fixture builds the project with
    # ``build_project=True``, leaving a populated DB at this path. Tests that depend
    # on that session fixture will have triggered the build before this autouse
    # fixture runs (session fixtures are always resolved before function-scoped
    # fixtures for a given test). For the rare test that doesn't use the session
    # fixture, the source may not exist — in that case we start with an empty DB.
    session_db_path = test_metadata_path / "target" / f"{db_file_name}.duckdb"
    if session_db_path.exists():
        shutil.copy(session_db_path, db_path)

    monkeypatch.setenv("DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_PATH", os.fspath(db_path))


def test_no_column_schema(test_jaffle_shop_manifest: dict[str, Any]) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path))},
    )

    assert result.success
    assert all(
        not TableMetadataSet.extract(event.materialization.metadata).column_schema
        for event in result.get_asset_materialization_events()
    )


@pytest.mark.parametrize(
    "use_experimental_fetch_column_schema",
    [True, False],
)
def test_column_schema(
    test_metadata_manifest: dict[str, Any],
    use_experimental_fetch_column_schema: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DBT_LOG_COLUMN_METADATA", str(not use_experimental_fetch_column_schema).lower()
    )

    @dbt_assets(manifest=test_metadata_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        cli_invocation = dbt.cli(["build"], context=context).stream()
        if use_experimental_fetch_column_schema:
            cli_invocation = cli_invocation.fetch_column_metadata(with_column_lineage=False)
        yield from cli_invocation

    customers_spec = my_dbt_assets.get_asset_spec(AssetKey(["customers"]))
    customer_spec_table_schema = TableMetadataSet.extract(customers_spec.metadata).column_schema

    # Ensure we get rich schema from schema.yml
    expected_customer_spec_table_schema = TableSchema(
        columns=[
            TableColumn(
                "customer_id",
                type="?",
                description="This is a unique identifier for a customer",
                constraints=TableColumnConstraints(nullable=True, unique=False),
                tags={"primary_key": ""},
            ),
            TableColumn(
                "first_name",
                type="?",
                description="Customer's first name. PII.",
                constraints=TableColumnConstraints(nullable=True, unique=False),
                tags={"pii": ""},
            ),
            TableColumn(
                "last_name",
                type="?",
                description="Customer's last name. PII.",
                constraints=TableColumnConstraints(nullable=True, unique=False),
                tags={"pii": ""},
            ),
            TableColumn(
                "first_order",
                type="?",
                description="Date (UTC) of a customer's first order",
                constraints=TableColumnConstraints(nullable=True, unique=False),
            ),
            TableColumn(
                "most_recent_order",
                type="?",
                description="Date (UTC) of a customer's most recent order",
                constraints=TableColumnConstraints(nullable=True, unique=False),
            ),
            TableColumn(
                "number_of_orders",
                type="?",
                description="Count of the number of orders a customer has placed",
                constraints=TableColumnConstraints(nullable=True, unique=False),
            ),
            TableColumn(
                "total_order_amount",
                type="?",
                description="Total value (AUD) of a customer's orders",
                constraints=TableColumnConstraints(nullable=True, unique=False),
            ),
        ]
    )
    assert customer_spec_table_schema == expected_customer_spec_table_schema

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_metadata_path))},
    )

    assert result.success

    table_schema_by_asset_key = {
        event.materialization.asset_key: TableMetadataSet.extract(
            event.materialization.metadata
        ).column_schema
        for event in result.get_asset_materialization_events()
        if event.materialization.asset_key == AssetKey(["customers"])
    }
    expected_table_schema_by_asset_key = {
        AssetKey(["customers"]): TableSchema(
            columns=[
                TableColumn("customer_id", type="INTEGER"),
                TableColumn("first_name", type="character varying(256)"),
                TableColumn("last_name", type="character varying(256)"),
                TableColumn("first_order", type="DATE"),
                TableColumn("most_recent_order", type="DATE"),
                TableColumn("number_of_orders", type="BIGINT"),
                TableColumn("customer_lifetime_value", type="DOUBLE"),
            ]
        ),
    }

    assert table_schema_by_asset_key == expected_table_schema_by_asset_key


def test_exception_fetch_column_schema_with_adapter(
    monkeypatch: pytest.MonkeyPatch, mocker: MockFixture, test_metadata_manifest: dict[str, Any]
):
    monkeypatch.setenv("DBT_LOG_COLUMN_METADATA", "false")

    mock_adapter = mocker.patch(
        "dagster_dbt.core.dbt_cli_invocation.DbtCliInvocation.adapter",
        return_value=mocker.MagicMock(),
        new_callable=mocker.PropertyMock,
    )
    mock_adapter.return_value.get_columns_in_relation.side_effect = Exception("An error occurred")

    @dbt_assets(manifest=test_metadata_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from (
            dbt.cli(["build"], context=context)
            .stream()
            .fetch_column_metadata(with_column_lineage=False)
        )

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_metadata_path))},
    )

    assert result.success
    assert all(
        not TableMetadataSet.extract(event.materialization.metadata).column_schema
        for event in result.get_asset_materialization_events()
    )


@pytest.mark.parametrize(
    "use_experimental_fetch_column_schema",
    [True, False],
)
def test_exception_column_schema(
    mocker: MockFixture,
    test_metadata_manifest: dict[str, Any],
    use_experimental_fetch_column_schema: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DBT_LOG_COLUMN_METADATA", str(not use_experimental_fetch_column_schema).lower()
    )
    mocker.patch(
        "dagster_dbt.core.dbt_cli_event.default_metadata_from_dbt_resource_props",
        side_effect=Exception("An error occurred"),
    )
    mocker.patch(
        "dagster_dbt.core.dbt_event_iterator.default_metadata_from_dbt_resource_props",
        side_effect=Exception("An error occurred"),
    )

    @dbt_assets(manifest=test_metadata_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        cli_invocation = dbt.cli(["build"], context=context).stream()
        if use_experimental_fetch_column_schema:
            cli_invocation = cli_invocation.fetch_column_metadata(with_column_lineage=False)
        yield from cli_invocation

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_metadata_path))},
    )

    assert result.success
    assert all(
        not TableMetadataSet.extract(event.materialization.metadata).column_schema
        for event in result.get_asset_materialization_events()
    )


def test_no_column_lineage(test_metadata_manifest: dict[str, Any]) -> None:
    @dbt_assets(manifest=test_metadata_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(
            [
                "build",
                "--vars",
                json.dumps({"dagster_enable_parent_relation_metadata_collection": False}),
            ],
            context=context,
        ).stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_metadata_path))},
    )

    assert result.success
    assert all(
        not TableMetadataSet.extract(event.materialization.metadata).column_lineage
        for event in result.get_asset_materialization_events()
    )


@pytest.mark.parametrize(
    "use_fetch_column_metadata",
    [True, False],
    ids=["adapter_path", "native_event_history_path"],
)
def test_column_lineage_uses_get_asset_spec_for_upstream_keys(
    test_metadata_manifest: dict[str, Any],
    use_fetch_column_metadata: bool,
) -> None:
    """Regression test for https://github.com/dagster-io/dagster/issues/33856.

    Column lineage upstream asset keys must be resolved via
    ``translator.get_asset_spec(...).key`` so that translators which customize
    translation only by overriding ``get_asset_spec`` (e.g.
    ``DbtProjectComponentTranslator``) produce lineage entries that point at the
    *translated* keys actually present in the asset graph, rather than at the
    default-derived keys returned by ``get_asset_key``.

    Exercised against both lineage-building paths through
    ``_build_column_lineage_metadata``:

    - ``adapter_path``: the post-run adapter-querying thread invoked when the
      user calls ``.fetch_column_metadata()``
      (``dbt_event_iterator._fetch_column_metadata``).
    - ``native_event_history_path``: the path driven by dbt's structured event
      history when ``has_column_lineage_metadata`` is ``True``
      (``dbt_cli_event._get_lineage_metadata``).
    """

    class SpecOverrideTranslator(DagsterDbtTranslator):
        def get_asset_spec(
            self,
            manifest: Mapping[str, Any],
            unique_id: str,
            project: DbtProject | None,
        ) -> AssetSpec:
            spec = super().get_asset_spec(manifest, unique_id, project)
            return spec.replace_attributes(key=AssetKey(["renamed", *spec.key.path]))

    translator = SpecOverrideTranslator()

    @dbt_assets(manifest=test_metadata_manifest, dagster_dbt_translator=translator)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        cli_invocation = dbt.cli(["build"], context=context).stream()
        if use_fetch_column_metadata:
            cli_invocation = cli_invocation.fetch_column_metadata()
        yield from cli_invocation

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_metadata_path))},
    )
    assert result.success

    upstream_keys_in_lineage: set[AssetKey] = set()
    for event in result.get_asset_materialization_events():
        lineage = TableMetadataSet.extract(event.materialization.metadata).column_lineage
        if lineage is None:
            continue
        for col_deps in lineage.deps_by_column.values():
            for dep in col_deps:
                upstream_keys_in_lineage.add(dep.asset_key)

    # We need at least one lineage entry for the assertion to be meaningful.
    assert upstream_keys_in_lineage, (
        "Expected at least one column lineage entry in the materialization metadata"
    )
    # Every upstream key referenced in column lineage must be the translated key
    # ("renamed/..."), not the default-derived key.
    for key in upstream_keys_in_lineage:
        assert key.path[0] == "renamed", (
            f"Upstream key {key} in column lineage was not translated via get_asset_spec"
        )


@pytest.mark.parametrize(
    "use_experimental_fetch_column_schema",
    [True, False],
)
def test_exception_column_lineage(
    mocker: MockFixture,
    test_metadata_manifest: dict[str, Any],
    use_experimental_fetch_column_schema: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DBT_LOG_COLUMN_METADATA", str(not use_experimental_fetch_column_schema).lower()
    )
    mocker.patch(
        "dagster_dbt.core.dbt_cli_event._build_column_lineage_metadata",
        side_effect=Exception("An error occurred"),
    )

    @dbt_assets(manifest=test_metadata_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        cli_invocation = dbt.cli(["build"], context=context).stream()
        if use_experimental_fetch_column_schema:
            cli_invocation = cli_invocation.fetch_column_metadata(with_column_lineage=False)
        yield from cli_invocation

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_metadata_path))},
    )

    assert result.success
    assert all(
        not TableMetadataSet.extract(event.materialization.metadata).column_lineage
        for event in result.get_asset_materialization_events()
    )


@pytest.fixture(name="test_metadata_manifest_snowflake")
def test_metadata_manifest_snowflake_fixture() -> dict[str, Any]:
    return _create_dbt_invocation(test_metadata_path, target="snowflake").get_artifact(
        "manifest.json"
    )


@pytest.fixture(name="test_metadata_manifest_bigquery")
def test_metadata_manifest_bigquery_fixture() -> dict[str, Any]:
    return _create_dbt_invocation(test_metadata_path, target="bigquery").get_artifact(
        "manifest.json"
    )


EXPECTED_COLUMN_LINEAGE_FOR_METADATA_PROJECT = {
    AssetKey(["raw_customers"]): None,
    AssetKey(["raw_payments"]): None,
    AssetKey(["raw_orders"]): None,
    AssetKey(["stg_payments"]): TableColumnLineage(
        deps_by_column={
            "payment_id": [TableColumnDep(asset_key=AssetKey(["raw_payments"]), column_name="id")],
            "order_id": [
                TableColumnDep(asset_key=AssetKey(["raw_payments"]), column_name="order_id")
            ],
            "payment_method": [
                TableColumnDep(asset_key=AssetKey(["raw_payments"]), column_name="payment_method")
            ],
            "amount": [TableColumnDep(asset_key=AssetKey(["raw_payments"]), column_name="amount")],
        }
    ),
    AssetKey(["stg_customers"]): TableColumnLineage(
        deps_by_column={
            "customer_id": [
                TableColumnDep(asset_key=AssetKey(["raw_source_customers"]), column_name="id")
            ],
            "first_name": [
                TableColumnDep(
                    asset_key=AssetKey(["raw_source_customers"]), column_name="first_name"
                )
            ],
            "last_name": [
                TableColumnDep(
                    asset_key=AssetKey(["raw_source_customers"]), column_name="last_name"
                )
            ],
        }
    ),
    AssetKey(["stg_orders"]): TableColumnLineage(
        deps_by_column={
            "order_id": [TableColumnDep(asset_key=AssetKey(["raw_orders"]), column_name="id")],
            "customer_id": [
                TableColumnDep(asset_key=AssetKey(["raw_orders"]), column_name="user_id")
            ],
            "order_date": [
                TableColumnDep(asset_key=AssetKey(["raw_orders"]), column_name="order_date")
            ],
            "status": [TableColumnDep(asset_key=AssetKey(["raw_orders"]), column_name="status")],
        }
    ),
    AssetKey(["orders"]): TableColumnLineage(
        deps_by_column={
            "order_id": [
                TableColumnDep(asset_key=AssetKey(["stg_orders"]), column_name="order_id")
            ],
            "customer_id": [
                TableColumnDep(asset_key=AssetKey(["stg_orders"]), column_name="customer_id")
            ],
            "order_date": [
                TableColumnDep(asset_key=AssetKey(["stg_orders"]), column_name="order_date")
            ],
            "status": [TableColumnDep(asset_key=AssetKey(["stg_orders"]), column_name="status")],
            "credit_card_amount": [
                TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="amount"),
                TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="payment_method"),
            ],
            "coupon_amount": [
                TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="amount"),
                TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="payment_method"),
            ],
            "bank_transfer_amount": [
                TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="amount"),
                TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="payment_method"),
            ],
            "gift_card_amount": [
                TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="amount"),
                TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="payment_method"),
            ],
            "amount": [
                TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="amount"),
            ],
        }
    ),
    AssetKey(["duplicate_column_dep_orders"]): TableColumnLineage(
        deps_by_column={
            "amount_2x": [TableColumnDep(asset_key=AssetKey(["orders"]), column_name="amount")],
        }
    ),
    AssetKey(["incremental_orders"]): TableColumnLineage(
        deps_by_column={
            "order_id": [TableColumnDep(asset_key=AssetKey(["orders"]), column_name="order_id")],
            "order_date": [
                TableColumnDep(asset_key=AssetKey(["orders"]), column_name="order_date")
            ],
        }
    ),
    AssetKey(["customers"]): TableColumnLineage(
        deps_by_column={
            "customer_id": [
                TableColumnDep(asset_key=AssetKey(["stg_customers"]), column_name="customer_id")
            ],
            "first_name": [
                TableColumnDep(asset_key=AssetKey(["stg_customers"]), column_name="first_name")
            ],
            "last_name": [
                TableColumnDep(asset_key=AssetKey(["stg_customers"]), column_name="last_name")
            ],
            "first_order": [
                TableColumnDep(asset_key=AssetKey(["stg_orders"]), column_name="order_date")
            ],
            "most_recent_order": [
                TableColumnDep(asset_key=AssetKey(["stg_orders"]), column_name="order_date")
            ],
            "number_of_orders": [
                TableColumnDep(asset_key=AssetKey(["stg_orders"]), column_name="order_id")
            ],
            "customer_lifetime_value": [
                TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="amount")
            ],
        }
    ),
    AssetKey(["select_star_customers"]): TableColumnLineage(
        deps_by_column={
            "customer_id": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="customer_id")
            ],
            "first_name": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="first_name")
            ],
            "last_name": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="last_name")
            ],
            "first_order": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="first_order")
            ],
            "most_recent_order": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="most_recent_order")
            ],
            "number_of_orders": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="number_of_orders")
            ],
            "customer_lifetime_value": [
                TableColumnDep(
                    asset_key=AssetKey(["customers"]), column_name="customer_lifetime_value"
                )
            ],
        }
    ),
    AssetKey(["count_star_customers"]): TableColumnLineage(
        deps_by_column={
            "count_star": [],
        }
    ),
    AssetKey(["count_star_implicit_alias_customers"]): TableColumnLineage(
        deps_by_column={
            "count_star()": [],
        }
    ),
}


@pytest.mark.parametrize(
    "target, manifest_fixture_name, excluded_models",
    [
        pytest.param(
            "snowflake",
            "test_metadata_manifest_snowflake",
            # No implicit alias allowed in Snowflake
            ["count_star_implicit_alias_customers"],
            marks=pytest.mark.snowflake,
            id="snowflake",
        ),
        pytest.param(
            "bigquery",
            "test_metadata_manifest_bigquery",
            # BigQuery does not support incremental_strategy='append'
            ["count_star_implicit_alias_customers", "incremental_orders"],
            marks=pytest.mark.bigquery,
            id="bigquery",
        ),
    ],
)
@pytest.mark.parametrize("fetch_row_counts", [True, False])
def test_column_lineage_real_warehouse(
    request: pytest.FixtureRequest,
    target: str,
    excluded_models: list[str] | None,
    fetch_row_counts: bool,
    manifest_fixture_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_metadata_manifest: dict[str, Any] = cast(
        "dict[str, Any]", request.getfixturevalue(manifest_fixture_name)
    )
    sql_dialect = target

    monkeypatch.setenv("DBT_LOG_COLUMN_METADATA", str(False).lower())

    manifest = test_metadata_manifest.copy()
    assert manifest["metadata"]["adapter_type"] == sql_dialect

    excluded_models = excluded_models or []

    dbt = DbtCliResource(project_dir=os.fspath(test_metadata_path), target=target)
    dbt.cli(["--quiet", "seed", "--exclude", "resource_type:test", *excluded_models]).wait()
    dbt.cli(
        [
            "--quiet",
            "build",
            # Exclude seeds to ensure they are built first
            "--exclude",
            "resource_type:seed",
            "--exclude",
            "resource_type:test",
            *excluded_models,
        ]
    ).wait()

    @dbt_assets(manifest=manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        seed_cli_invocation = dbt.cli(
            ["seed"],
            context=context,
        ).stream()
        if fetch_row_counts:
            seed_cli_invocation = seed_cli_invocation.fetch_row_counts()
        seed_cli_invocation = seed_cli_invocation.fetch_column_metadata()
        yield from seed_cli_invocation

        cli_invocation = dbt.cli(
            ["build", "--exclude", "resource_type:seed", *excluded_models],
            context=context,
        ).stream()
        if fetch_row_counts:
            cli_invocation = cli_invocation.fetch_row_counts()
        cli_invocation = cli_invocation.fetch_column_metadata()
        yield from cli_invocation

    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success

    column_lineage_by_asset_key = {
        event.materialization.asset_key: TableMetadataSet.extract(
            event.materialization.metadata
        ).column_lineage
        for event in result.get_asset_materialization_events()
    }

    expected_column_lineage_by_asset_key = {
        k: v
        for k, v in EXPECTED_COLUMN_LINEAGE_FOR_METADATA_PROJECT.items()
        if k.path[-1] not in excluded_models
    }
    assert column_lineage_by_asset_key == expected_column_lineage_by_asset_key, (
        str(column_lineage_by_asset_key)
        + "\n\n"
        + str(EXPECTED_COLUMN_LINEAGE_FOR_METADATA_PROJECT)
    )


def _is_master_branch() -> bool:
    return os.environ.get("BUILDKITE_BRANCH") == "master"


# Representative cases that always run on every branch. The remainder of the
# sql_dialect x use_async x selection cross product is gated behind a master-
# only skip below; that lets master detect any coverage gap in either this
# reduced set or in the direct dialect unit tests, while keeping PR-time
# runtime down.
_REPRESENTATIVE_INTEGRATION_KEYS: set[tuple[bool, AssetKey | None, str]] = {
    (True, None, "duckdb"),
    (False, None, "duckdb"),
    (True, AssetKey(["raw_customers"]), "duckdb"),
    (True, AssetKey(["stg_customers"]), "duckdb"),
    (True, AssetKey(["customers"]), "duckdb"),
    (True, AssetKey(["select_star_customers"]), "duckdb"),
}


def _build_integration_lineage_cases() -> list[ParameterSet]:
    skip_on_feature_branch = pytest.mark.skipif(
        not _is_master_branch(),
        reason="Full integration matrix runs only on master; PRs use representative cases.",
    )
    cases: list[ParameterSet] = []
    for use_async in [True, False]:
        for sql_dialect in ["bigquery", "databricks", "duckdb", "snowflake", "trino"]:
            for selection in [
                None,
                AssetKey(["raw_customers"]),
                AssetKey(["stg_customers"]),
                AssetKey(["customers"]),
                AssetKey(["select_star_customers"]),
            ]:
                key = (use_async, selection, sql_dialect)
                marks = () if key in _REPRESENTATIVE_INTEGRATION_KEYS else (skip_on_feature_branch,)
                metadata_id = "async" if use_async else "legacy"
                selection_id = selection.path[-1] if selection else "all"
                cases.append(
                    pytest.param(
                        sql_dialect,
                        use_async,
                        selection,
                        marks=marks,
                        id=f"{metadata_id}-{sql_dialect}-{selection_id}",
                    )
                )
    return cases


@pytest.mark.parametrize(
    "sql_dialect,use_async_fetch_column_schema,asset_key_selection",
    _build_integration_lineage_cases(),
)
def test_column_lineage_integration(
    sql_dialect: str,
    test_metadata_manifest: dict[str, Any],
    asset_key_selection: AssetKey | None,
    use_async_fetch_column_schema: bool,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockFixture,
    capsys,
) -> None:
    # Patch get_relation_from_adapter so that we can track how often
    # relations are queried from the adapter vs cached
    from dagster_dbt.core.dbt_cli_invocation import _get_relation_from_adapter

    get_relation_from_adapter = mocker.patch(
        "dagster_dbt.core.dbt_cli_invocation._get_relation_from_adapter",
        side_effect=_get_relation_from_adapter,
    )

    monkeypatch.setenv("DBT_LOG_COLUMN_METADATA", str(not use_async_fetch_column_schema).lower())
    # Simulate the parsing of the SQL into a different dialect.
    assert Dialect.get_or_raise(sql_dialect)

    manifest = test_metadata_manifest.copy()
    manifest["metadata"]["adapter_type"] = sql_dialect

    dbt = DbtCliResource(project_dir=os.fspath(test_metadata_path))
    # Pre-build so column metadata (types, lineage) is available for the
    # fetch_column_metadata assertions below.
    dbt.cli(["--quiet", "seed"]).wait()
    dbt.cli(["--quiet", "build", "--exclude", "resource_type:test"]).wait()

    @dbt_assets(manifest=manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        cli_invocation = dbt.cli(["build"], context=context).stream()
        if use_async_fetch_column_schema:
            cli_invocation = cli_invocation.fetch_column_metadata()
        yield from cli_invocation

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": dbt},
        selection=AssetSelection.assets(asset_key_selection) if asset_key_selection else None,
    )

    # Check that the warning is printed only when using log_column_level_metadata
    if not use_async_fetch_column_schema:
        assert "`log_column_level_metadata` macro is deprecated" in capsys.readouterr().err

    column_lineage_by_asset_key = {
        event.materialization.asset_key: TableMetadataSet.extract(
            event.materialization.metadata
        ).column_lineage
        for event in result.get_asset_materialization_events()
    }

    expected_column_lineage_by_asset_key = EXPECTED_COLUMN_LINEAGE_FOR_METADATA_PROJECT
    if asset_key_selection:
        expected_column_lineage_by_asset_key = {
            asset_key: deps_by_column
            for asset_key, deps_by_column in expected_column_lineage_by_asset_key.items()
            if asset_key == asset_key_selection
        }

    assert column_lineage_by_asset_key == expected_column_lineage_by_asset_key, (
        str(column_lineage_by_asset_key) + "\n\n" + str(expected_column_lineage_by_asset_key)
    )

    # Ensure we cache relation metadata fetches
    if use_async_fetch_column_schema:
        relation_keys_passed = [
            call.kwargs["relation_key"] for call in get_relation_from_adapter.call_args_list
        ]
        # We may query the same relation multiple times if they initiate at around the same time.
        # Still, the total number of unique relations queried should be a lot lower than the total
        # number of instances where we get column metadata (around 33 instead of 60+)
        REPEAT_QUERIES_PADDING = 10
        assert len(relation_keys_passed) <= len(set(relation_keys_passed)) + REPEAT_QUERIES_PADDING


@pytest.mark.parametrize(
    "command",
    ["parse", "build"],
    ids=[
        "no empty jinja log info on parse",
        "no jinja log info on execution",
    ],
)
def test_dbt_raw_cli_no_jinja_log_info(
    test_metadata_manifest: dict[str, Any], command: str
) -> None:
    result = subprocess.check_output(
        ["dbt", "--log-format", "json", "--no-partial-parse", command],
        text=True,
        cwd=test_metadata_path,
    )

    assert not any(
        json.loads(line)["info"]["name"] == "JinjaLogInfo" for line in result.splitlines()
    )


EXPECTED_COLUMN_LINEAGE_FOR_DEPENDENCIES_PROJECT = {
    **{
        key: value
        for key, value in EXPECTED_COLUMN_LINEAGE_FOR_METADATA_PROJECT.items()
        if key
        in (
            AssetKey(["raw_customers"]),
            AssetKey(["raw_payments"]),
            AssetKey(["raw_orders"]),
            AssetKey(["stg_payments"]),
            AssetKey(["stg_customers"]),
            AssetKey(["stg_orders"]),
            AssetKey(["orders"]),
            AssetKey(["customers"]),
        )
    },
    AssetKey(["stg_customers"]): TableColumnLineage(
        deps_by_column={
            "customer_id": [
                TableColumnDep(asset_key=AssetKey(["raw_customers"]), column_name="id")
            ],
            "first_name": [
                TableColumnDep(asset_key=AssetKey(["raw_customers"]), column_name="first_name")
            ],
            "last_name": [
                TableColumnDep(asset_key=AssetKey(["raw_customers"]), column_name="last_name")
            ],
        }
    ),
    AssetKey(["customers_refined"]): TableColumnLineage(
        deps_by_column={
            "customer_id": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="customer_id")
            ],
            "first_name": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="first_name")
            ],
            "last_name": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="last_name")
            ],
            "first_order": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="first_order")
            ],
            "most_recent_order": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="most_recent_order")
            ],
            "number_of_orders": [
                TableColumnDep(asset_key=AssetKey(["customers"]), column_name="number_of_orders")
            ],
            "customer_lifetime_value": [
                TableColumnDep(
                    asset_key=AssetKey(["customers"]), column_name="customer_lifetime_value"
                )
            ],
        }
    ),
}


@pytest.mark.parametrize(
    "use_windows_manifest",
    [False, True],
)
def test_column_lineage_dependencies(
    test_dependencies_manifest: dict[str, Any],
    test_dependencies_manifest_windows: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockFixture,
    capsys,
    use_windows_manifest: bool,
) -> None:
    # Patch get_relation_from_adapter so that we can track how often
    # relations are queried from the adapter vs cached

    monkeypatch.setenv("DBT_LOG_COLUMN_METADATA", str(False).lower())

    dbt = DbtCliResource(project_dir=os.fspath(test_dependencies_path))
    dbt.cli(["--quiet", "build", "--exclude", "resource_type:test"]).wait()

    @dbt_assets(
        manifest=test_dependencies_manifest_windows
        if use_windows_manifest
        else test_dependencies_manifest
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        cli_invocation = dbt.cli(["build"], context=context).stream().fetch_column_metadata()
        yield from cli_invocation

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": dbt},
    )

    column_lineage_by_asset_key = {
        event.materialization.asset_key: TableMetadataSet.extract(
            event.materialization.metadata
        ).column_lineage
        for event in result.get_asset_materialization_events()
    }

    expected_column_lineage_by_asset_key = EXPECTED_COLUMN_LINEAGE_FOR_DEPENDENCIES_PROJECT

    assert column_lineage_by_asset_key == expected_column_lineage_by_asset_key, (
        str(column_lineage_by_asset_key) + "\n\n" + str(expected_column_lineage_by_asset_key)
    )


def test_get_compiled_sql_prefers_compiled_file(tmp_path: Path) -> None:
    dbt_resource_props = {
        "package_name": "my_project",
        "original_file_path": "models/my_model.sql",
        "compiled_code": "select 'from_manifest' as col",
    }
    compiled_path = tmp_path / "compiled" / "my_project" / "models"
    compiled_path.mkdir(parents=True)
    compiled_path.joinpath("my_model.sql").write_text("select 'from_file' as col")

    assert _get_compiled_sql(dbt_resource_props, tmp_path) == "select 'from_file' as col"


def test_get_compiled_sql_falls_back_to_invocation_manifest(tmp_path: Path) -> None:
    """Snapshots have no file under ``target/compiled/`` because dbt does not write one, so the
    compiled code recorded in the manifest the invocation wrote must be used instead. The manifest
    Dagster is configured with is frequently produced by ``dbt parse``, which does not compile and
    leaves ``compiled_code`` null. See https://github.com/dagster-io/dagster/issues/34124.
    """
    unique_id = "snapshot.my_project.my_snapshot"
    dbt_resource_props = {
        "unique_id": unique_id,
        "package_name": "my_project",
        "original_file_path": "snapshots/my_snapshot.sql",
        # As left by `dbt parse`.
        "compiled_code": None,
    }
    tmp_path.joinpath("manifest.json").write_text(
        json.dumps(
            {"nodes": {unique_id: {"compiled_code": "select 'from_invocation_manifest' as col"}}}
        )
    )

    assert (
        _get_compiled_sql(dbt_resource_props, tmp_path)
        == "select 'from_invocation_manifest' as col"
    )


def test_get_compiled_sql_prefers_invocation_manifest_over_configured_manifest(
    tmp_path: Path,
) -> None:
    """The manifest Dagster is configured with may carry compiled code that predates the invocation,
    e.g. when the run changes the compiled SQL through project edits, vars, target or state. Lineage
    must describe the SQL the invocation actually ran, so the invocation's own manifest wins.
    """
    unique_id = "snapshot.my_project.my_snapshot"
    dbt_resource_props = {
        "unique_id": unique_id,
        "package_name": "my_project",
        "original_file_path": "snapshots/my_snapshot.sql",
        "compiled_code": "select 'stale_configured_manifest' as col",
    }
    tmp_path.joinpath("manifest.json").write_text(
        json.dumps(
            {"nodes": {unique_id: {"compiled_code": "select 'from_invocation_manifest' as col"}}}
        )
    )

    assert (
        _get_compiled_sql(dbt_resource_props, tmp_path)
        == "select 'from_invocation_manifest' as col"
    )


def test_get_compiled_sql_rereads_rewritten_invocation_manifest(tmp_path: Path) -> None:
    """The invocation manifest is cached so that it is parsed once rather than once per node, but
    invocations that pin ``target_path`` write the same path more than once. A rewrite must not be
    served from the cache, or the second run emits the first run's lineage.

    The rewrite here is made deliberately indistinguishable by ``stat``: the same file size, and the
    same mtime down to the nanosecond. That is what a same-size rewrite looks like on a filesystem
    whose timestamp granularity is coarser than the gap between the two writes, so the cache cannot
    treat mtime and size as an identity for the file's contents.
    """
    unique_id = "snapshot.my_project.my_snapshot"
    dbt_resource_props = {
        "unique_id": unique_id,
        "package_name": "my_project",
        "original_file_path": "snapshots/my_snapshot.sql",
        "compiled_code": None,
    }
    manifest_path = tmp_path / "manifest.json"

    def write_manifest(compiled_code: str) -> None:
        manifest_path.write_text(
            json.dumps({"nodes": {unique_id: {"compiled_code": compiled_code}}})
        )

    write_manifest("select 'first_invocation' as col")
    original_stat = manifest_path.stat()
    assert _get_compiled_sql(dbt_resource_props, tmp_path) == "select 'first_invocation' as col"

    # The cached entry is keyed on a digest of the bytes it was parsed from.
    cached_digest, _ = check.not_none(dbt_cli_event._compiled_code_cache)  # noqa: SLF001
    assert cached_digest == hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    # Same length as the first manifest, restored to the same mtime, so neither is distinguishable
    # from the other by `stat`.
    write_manifest("select 'third_invocation' as col")
    os.utime(manifest_path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    rewritten_stat = manifest_path.stat()
    assert (rewritten_stat.st_size, rewritten_stat.st_mtime_ns) == (
        original_stat.st_size,
        original_stat.st_mtime_ns,
    )

    assert _get_compiled_sql(dbt_resource_props, tmp_path) == "select 'third_invocation' as col"


def test_get_compiled_sql_reuses_cached_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unchanged manifest is parsed once rather than once per node. Proven by making a second
    parse impossible: with the manifest untouched, the cached mapping must be returned without
    ``json`` being consulted again.
    """
    unique_id = "snapshot.my_project.my_snapshot"
    dbt_resource_props = {
        "unique_id": unique_id,
        "package_name": "my_project",
        "original_file_path": "snapshots/my_snapshot.sql",
        "compiled_code": None,
    }
    tmp_path.joinpath("manifest.json").write_text(
        json.dumps({"nodes": {unique_id: {"compiled_code": "select 'parsed_once' as col"}}})
    )

    assert _get_compiled_sql(dbt_resource_props, tmp_path) == "select 'parsed_once' as col"

    def fail_if_parsed(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("manifest was parsed again instead of being served from the cache")

    # Patched on the module rather than on `json` itself, so nothing else in the process is affected.
    monkeypatch.setattr(dbt_cli_event, "json", SimpleNamespace(loads=fail_if_parsed))

    assert _get_compiled_sql(dbt_resource_props, tmp_path) == "select 'parsed_once' as col"


def test_get_compiled_sql_parses_the_bytes_it_digested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The cache key and the parsed mapping must come from a single read of the manifest.

    If the digest were computed from one read and the mapping parsed from another, a rewrite landing
    between them would cache the replacement manifest's SQL under the previous manifest's digest, and
    any later invocation whose manifest hashed to that digest would be served the wrong SQL. Simulated
    by rewriting the file from inside the digest call, which is the point between the two reads.
    """
    unique_id = "snapshot.my_project.my_snapshot"
    dbt_resource_props = {
        "unique_id": unique_id,
        "package_name": "my_project",
        "original_file_path": "snapshots/my_snapshot.sql",
        "compiled_code": None,
    }
    manifest_path = tmp_path / "manifest.json"

    def write_manifest(compiled_code: str) -> None:
        manifest_path.write_text(
            json.dumps({"nodes": {unique_id: {"compiled_code": compiled_code}}})
        )

    write_manifest("select 'digested_manifest' as col")
    digested_bytes = manifest_path.read_bytes()

    sha256 = hashlib.sha256

    def rewrite_manifest_then_digest(*args: Any, **kwargs: Any) -> "hashlib._Hash":
        write_manifest("select 'rewritten_manifest' as col")
        return sha256(*args, **kwargs)

    monkeypatch.setattr(
        dbt_cli_event, "hashlib", SimpleNamespace(sha256=rewrite_manifest_then_digest)
    )

    # The bytes that were digested are the bytes that get parsed, even though the file on disk has
    # since been replaced.
    assert _get_compiled_sql(dbt_resource_props, tmp_path) == "select 'digested_manifest' as col"

    # And the entry is stored under the digest of those same bytes, so it cannot be served for the
    # manifest now on disk.
    cached_digest, _ = check.not_none(dbt_cli_event._compiled_code_cache)  # noqa: SLF001
    assert cached_digest == sha256(digested_bytes).hexdigest()


def test_get_compiled_sql_falls_back_to_configured_manifest(tmp_path: Path) -> None:
    """The invocation manifest is only written once the invocation finishes, so it may be absent
    when a node's metadata is fetched mid-run. The configured manifest is the last resort.
    """
    dbt_resource_props = {
        "unique_id": "snapshot.my_project.my_snapshot",
        "package_name": "my_project",
        "original_file_path": "snapshots/my_snapshot.sql",
        "compiled_code": "select 'from_configured_manifest' as col",
    }

    assert (
        _get_compiled_sql(dbt_resource_props, tmp_path)
        == "select 'from_configured_manifest' as col"
    )


def test_get_compiled_sql_returns_none_when_unavailable(tmp_path: Path) -> None:
    dbt_resource_props = {
        "unique_id": "snapshot.my_project.my_snapshot",
        "package_name": "my_project",
        "original_file_path": "snapshots/my_snapshot.sql",
    }

    assert _get_compiled_sql(dbt_resource_props, tmp_path) is None

    # A manifest that has no compiled code for the node is also handled.
    tmp_path.joinpath("manifest.json").write_text(json.dumps({"nodes": {}}))

    assert _get_compiled_sql(dbt_resource_props, tmp_path) is None


def test_column_lineage_snapshot(
    test_dbt_snapshot_column_lineage_manifest: dict[str, Any],
) -> None:
    """Column lineage must be produced for dbt snapshots.

    dbt intentionally does not write compiled snapshot SQL to ``target/compiled/`` (see
    ``Compiler._write_node``), so resolving it only from that path raised ``FileNotFoundError``,
    which was swallowed in ``_fetch_column_metadata``, leaving snapshots with no lineage at all.
    See https://github.com/dagster-io/dagster/issues/34124.

    Only the adapter path is exercised here (``.fetch_column_metadata()``, the repro in the
    issue); the dbt-event-history path resolves compiled SQL through the same
    ``_build_column_lineage_metadata`` call, and ``_get_compiled_sql`` is covered directly above.
    """
    dbt = DbtCliResource(project_dir=os.fspath(test_dbt_snapshot_column_lineage_path))

    @dbt_assets(manifest=test_dbt_snapshot_column_lineage_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream().fetch_column_metadata()

    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success

    column_lineage_by_asset_key = {
        event.materialization.asset_key: TableMetadataSet.extract(
            event.materialization.metadata
        ).column_lineage
        for event in result.get_asset_materialization_events()
    }

    snapshot_lineage = column_lineage_by_asset_key[AssetKey(["customers_snapshot"])]
    assert snapshot_lineage is not None, (
        f"Expected column lineage for the snapshot, got none: {column_lineage_by_asset_key}"
    )

    # The snapshot's own columns are derived from the model it selects from.
    for column_name in ("customer_id", "first_name", "last_name"):
        assert snapshot_lineage.deps_by_column[column_name] == [
            TableColumnDep(asset_key=AssetKey(["stg_customers"]), column_name=column_name)
        ]

    # dbt adds its own bookkeeping columns to the snapshot relation. They are not selected in the
    # compiled SQL, so they have no upstream dependencies. Asserted loosely because which columns
    # dbt adds varies across the supported dbt versions.
    for column_name, column_deps in snapshot_lineage.deps_by_column.items():
        if column_name in ("customer_id", "first_name", "last_name"):
            continue

        assert column_name.startswith("dbt_"), (
            f"Unexpected column `{column_name}` in snapshot column lineage"
        )
        assert column_deps == []
