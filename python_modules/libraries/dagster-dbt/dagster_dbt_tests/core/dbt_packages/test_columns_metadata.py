import json
import os
import subprocess
from typing import Any, Dict, List, Optional, cast

import pytest
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSelection,
    TableColumn,
    TableColumnDep,
    TableColumnLineage,
    TableSchema,
    materialize,
)
from dagster._core.definitions.metadata import TableMetadataSet
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core.resource import DbtCliResource
from pytest_mock import MockFixture
from sqlglot import Dialect

from dagster_dbt_tests.conftest import _create_dbt_invocation
from dagster_dbt_tests.dbt_projects import test_jaffle_shop_path, test_metadata_path

pytestmark: pytest.MarkDecorator = pytest.mark.derived_metadata


def test_no_column_schema(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
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
    test_metadata_manifest: Dict[str, Any],
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
    monkeypatch: pytest.MonkeyPatch, mocker: MockFixture, test_metadata_manifest: Dict[str, Any]
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
    test_metadata_manifest: Dict[str, Any],
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


def test_no_column_lineage(test_metadata_manifest: Dict[str, Any]) -> None:
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
    "use_experimental_fetch_column_schema",
    [True, False],
)
def test_exception_column_lineage(
    mocker: MockFixture,
    test_metadata_manifest: Dict[str, Any],
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
def test_metadata_manifest_snowflake_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_metadata_path, target="snowflake").get_artifact(
        "manifest.json"
    )


@pytest.fixture(name="test_metadata_manifest_bigquery")
def test_metadata_manifest_bigquery_fixture() -> Dict[str, Any]:
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
    excluded_models: Optional[List[str]],
    fetch_row_counts: bool,
    manifest_fixture_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_metadata_manifest: Dict[str, Any] = cast(
        Dict[str, Any], request.getfixturevalue(manifest_fixture_name)
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


@pytest.mark.parametrize(
    "asset_key_selection",
    [
        None,
        AssetKey(["raw_customers"]),
        AssetKey(["stg_customers"]),
        AssetKey(["customers"]),
        AssetKey(["select_star_customers"]),
    ],
    ids=[
        "--select fqn:*",
        "--select raw_customers",
        "--select stg_customers",
        "--select customers",
        "--select select_star_customers",
    ],
)
@pytest.mark.parametrize(
    "sql_dialect",
    [
        "bigquery",
        "databricks",
        "duckdb",
        "snowflake",
        "trino",
    ],
)
@pytest.mark.parametrize(
    "use_async_fetch_column_schema",
    [True, False],
)
def test_column_lineage(
    sql_dialect: str,
    test_metadata_manifest: Dict[str, Any],
    asset_key_selection: Optional[AssetKey],
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
        selection=asset_key_selection and AssetSelection.assets(asset_key_selection),
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
    test_metadata_manifest: Dict[str, Any], command: str
) -> None:
    result = subprocess.check_output(
        ["dbt", "--log-format", "json", "--no-partial-parse", command],
        text=True,
        cwd=test_metadata_path,
    )

    assert not any(
        json.loads(line)["info"]["name"] == "JinjaLogInfo" for line in result.splitlines()
    )
