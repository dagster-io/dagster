import json
import os
import subprocess
from typing import Any, Dict, Optional

import pytest
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSelection,
    TableColumn,
    TableSchema,
    materialize,
)
from dagster._core.definitions.metadata import TableMetadataEntries
from dagster._core.definitions.metadata.table import (
    TableColumnDep,
    TableColumnLineage,
)
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core.resources_v2 import DbtCliResource
from dbt.version import __version__ as dbt_version
from packaging import version

from ...dbt_projects import test_jaffle_shop_path, test_metadata_path


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
        not TableMetadataEntries.extract(event.materialization.metadata).column_schema
        for event in result.get_asset_materialization_events()
    )


def test_column_schema(test_metadata_manifest: Dict[str, Any]) -> None:
    @dbt_assets(manifest=test_metadata_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_metadata_path))},
    )

    assert result.success

    table_schema_by_asset_key = {
        event.materialization.asset_key: TableMetadataEntries.extract(
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


@pytest.mark.skipif(
    version.parse(dbt_version) < version.parse("1.6.0"),
    reason="Retrieving the dbt project name from the manifest is only available in `dbt-core>=1.6`",
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
        not TableMetadataEntries.extract(event.materialization.metadata).column_lineage
        for event in result.get_asset_materialization_events()
    )


@pytest.mark.skipif(
    version.parse(dbt_version) < version.parse("1.6.0"),
    reason="Retrieving the dbt project name from the manifest is only available in `dbt-core>=1.6`",
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
def test_column_lineage(
    test_metadata_manifest: Dict[str, Any], asset_key_selection: Optional[AssetKey]
) -> None:
    @dbt_assets(manifest=test_metadata_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_metadata_path))},
        selection=asset_key_selection and AssetSelection.keys(asset_key_selection),
    )
    assert result.success

    column_lineage_by_asset_key = {
        event.materialization.asset_key: TableMetadataEntries.extract(
            event.materialization.metadata
        ).column_lineage
        for event in result.get_asset_materialization_events()
    }
    expected_column_lineage_by_asset_key = {
        AssetKey(["raw_customers"]): None,
        AssetKey(["raw_payments"]): None,
        AssetKey(["raw_orders"]): None,
        AssetKey(["stg_payments"]): TableColumnLineage(
            deps_by_column={
                "payment_id": [
                    TableColumnDep(asset_key=AssetKey(["raw_payments"]), column_name="id")
                ],
                "order_id": [
                    TableColumnDep(asset_key=AssetKey(["raw_payments"]), column_name="order_id")
                ],
                "payment_method": [
                    TableColumnDep(
                        asset_key=AssetKey(["raw_payments"]), column_name="payment_method"
                    )
                ],
                "amount": [
                    TableColumnDep(asset_key=AssetKey(["raw_payments"]), column_name="amount")
                ],
            }
        ),
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
        AssetKey(["stg_orders"]): TableColumnLineage(
            deps_by_column={
                "order_id": [TableColumnDep(asset_key=AssetKey(["raw_orders"]), column_name="id")],
                "customer_id": [
                    TableColumnDep(asset_key=AssetKey(["raw_orders"]), column_name="user_id")
                ],
                "order_date": [
                    TableColumnDep(asset_key=AssetKey(["raw_orders"]), column_name="order_date")
                ],
                "status": [
                    TableColumnDep(asset_key=AssetKey(["raw_orders"]), column_name="status")
                ],
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
                "status": [
                    TableColumnDep(asset_key=AssetKey(["stg_orders"]), column_name="status")
                ],
                "credit_card_amount": [
                    TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="amount")
                ],
                "coupon_amount": [
                    TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="amount")
                ],
                "bank_transfer_amount": [
                    TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="amount")
                ],
                "gift_card_amount": [
                    TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="amount")
                ],
                "amount": [
                    TableColumnDep(asset_key=AssetKey(["stg_payments"]), column_name="amount")
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
                    TableColumnDep(
                        asset_key=AssetKey(["customers"]), column_name="most_recent_order"
                    )
                ],
                "number_of_orders": [
                    TableColumnDep(
                        asset_key=AssetKey(["customers"]), column_name="number_of_orders"
                    )
                ],
                "customer_lifetime_value": [
                    TableColumnDep(
                        asset_key=AssetKey(["customers"]), column_name="customer_lifetime_value"
                    )
                ],
            }
        ),
    }
    if asset_key_selection:
        expected_column_lineage_by_asset_key = {
            asset_key: deps_by_column
            for asset_key, deps_by_column in expected_column_lineage_by_asset_key.items()
            if asset_key == asset_key_selection
        }

    assert column_lineage_by_asset_key == expected_column_lineage_by_asset_key


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
