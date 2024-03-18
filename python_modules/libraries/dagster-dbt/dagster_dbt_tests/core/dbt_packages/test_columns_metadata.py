import json
import os
import subprocess
from typing import Any, Dict, Optional

import pytest
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSelection,
    JsonMetadataValue,
    TableColumn,
    TableSchema,
    materialize,
)
from dagster._core.definitions.metadata import TableMetadataEntries
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
def test_no_lineage(test_metadata_manifest: Dict[str, Any]) -> None:
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
        not event.materialization.metadata.get("dagster/column_lineage")
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
def test_lineage(
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

    lineage_metadata_by_asset_key = {
        event.materialization.asset_key: event.materialization.metadata.get(
            "dagster/column_lineage"
        )
        for event in result.get_asset_materialization_events()
    }
    expected_lineage_metadata_by_asset_key = {
        AssetKey(["raw_payments"]): None,
        AssetKey(["raw_customers"]): None,
        AssetKey(["raw_orders"]): None,
        AssetKey(["stg_customers"]): JsonMetadataValue(
            data={
                "customer_id": [
                    {
                        "upstream_asset_key": AssetKey(["raw_customers"]),
                        "upstream_column_name": "id",
                    }
                ],
                "first_name": [
                    {
                        "upstream_asset_key": AssetKey(["raw_customers"]),
                        "upstream_column_name": "first_name",
                    }
                ],
                "last_name": [
                    {
                        "upstream_asset_key": AssetKey(["raw_customers"]),
                        "upstream_column_name": "last_name",
                    }
                ],
            }
        ),
        AssetKey(["stg_orders"]): JsonMetadataValue(
            data={
                "order_id": [
                    {
                        "upstream_asset_key": AssetKey(["raw_orders"]),
                        "upstream_column_name": "id",
                    }
                ],
                "customer_id": [
                    {
                        "upstream_asset_key": AssetKey(["raw_orders"]),
                        "upstream_column_name": "user_id",
                    }
                ],
                "order_date": [
                    {
                        "upstream_asset_key": AssetKey(["raw_orders"]),
                        "upstream_column_name": "order_date",
                    }
                ],
                "status": [
                    {
                        "upstream_asset_key": AssetKey(["raw_orders"]),
                        "upstream_column_name": "status",
                    }
                ],
            }
        ),
        AssetKey(["stg_payments"]): JsonMetadataValue(
            data={
                "payment_id": [
                    {
                        "upstream_asset_key": AssetKey(["raw_payments"]),
                        "upstream_column_name": "id",
                    }
                ],
                "order_id": [
                    {
                        "upstream_asset_key": AssetKey(["raw_payments"]),
                        "upstream_column_name": "order_id",
                    }
                ],
                "payment_method": [
                    {
                        "upstream_asset_key": AssetKey(["raw_payments"]),
                        "upstream_column_name": "payment_method",
                    }
                ],
                "amount": [
                    {
                        "upstream_asset_key": AssetKey(["raw_payments"]),
                        "upstream_column_name": "amount",
                    }
                ],
            }
        ),
        AssetKey(["orders"]): JsonMetadataValue(
            data={
                "order_id": [
                    {
                        "upstream_asset_key": AssetKey(["stg_orders"]),
                        "upstream_column_name": "order_id",
                    }
                ],
                "customer_id": [
                    {
                        "upstream_asset_key": AssetKey(["stg_orders"]),
                        "upstream_column_name": "customer_id",
                    }
                ],
                "order_date": [
                    {
                        "upstream_asset_key": AssetKey(["stg_orders"]),
                        "upstream_column_name": "order_date",
                    }
                ],
                "status": [
                    {
                        "upstream_asset_key": AssetKey(["stg_orders"]),
                        "upstream_column_name": "status",
                    }
                ],
                "credit_card_amount": [
                    {
                        "upstream_asset_key": AssetKey(["stg_payments"]),
                        "upstream_column_name": "amount",
                    }
                ],
                "coupon_amount": [
                    {
                        "upstream_asset_key": AssetKey(["stg_payments"]),
                        "upstream_column_name": "amount",
                    }
                ],
                "bank_transfer_amount": [
                    {
                        "upstream_asset_key": AssetKey(["stg_payments"]),
                        "upstream_column_name": "amount",
                    }
                ],
                "gift_card_amount": [
                    {
                        "upstream_asset_key": AssetKey(["stg_payments"]),
                        "upstream_column_name": "amount",
                    }
                ],
                "amount": [
                    {
                        "upstream_asset_key": AssetKey(["stg_payments"]),
                        "upstream_column_name": "amount",
                    }
                ],
            }
        ),
        AssetKey(["customers"]): JsonMetadataValue(
            data={
                "customer_id": [
                    {
                        "upstream_asset_key": AssetKey(["stg_customers"]),
                        "upstream_column_name": "customer_id",
                    }
                ],
                "first_name": [
                    {
                        "upstream_asset_key": AssetKey(["stg_customers"]),
                        "upstream_column_name": "first_name",
                    }
                ],
                "last_name": [
                    {
                        "upstream_asset_key": AssetKey(["stg_customers"]),
                        "upstream_column_name": "last_name",
                    }
                ],
                "first_order": [
                    {
                        "upstream_asset_key": AssetKey(["stg_orders"]),
                        "upstream_column_name": "order_date",
                    }
                ],
                "most_recent_order": [
                    {
                        "upstream_asset_key": AssetKey(["stg_orders"]),
                        "upstream_column_name": "order_date",
                    }
                ],
                "number_of_orders": [
                    {
                        "upstream_asset_key": AssetKey(["stg_orders"]),
                        "upstream_column_name": "order_id",
                    }
                ],
                "customer_lifetime_value": [
                    {
                        "upstream_asset_key": AssetKey(["stg_payments"]),
                        "upstream_column_name": "amount",
                    }
                ],
            }
        ),
        AssetKey(["select_star_customers"]): JsonMetadataValue(
            data={
                "customer_id": [
                    {
                        "upstream_asset_key": AssetKey(["customers"]),
                        "upstream_column_name": "customer_id",
                    }
                ],
                "first_name": [
                    {
                        "upstream_asset_key": AssetKey(["customers"]),
                        "upstream_column_name": "first_name",
                    }
                ],
                "last_name": [
                    {
                        "upstream_asset_key": AssetKey(["customers"]),
                        "upstream_column_name": "last_name",
                    }
                ],
                "first_order": [
                    {
                        "upstream_asset_key": AssetKey(["customers"]),
                        "upstream_column_name": "first_order",
                    }
                ],
                "most_recent_order": [
                    {
                        "upstream_asset_key": AssetKey(["customers"]),
                        "upstream_column_name": "most_recent_order",
                    }
                ],
                "number_of_orders": [
                    {
                        "upstream_asset_key": AssetKey(["customers"]),
                        "upstream_column_name": "number_of_orders",
                    }
                ],
                "customer_lifetime_value": [
                    {
                        "upstream_asset_key": AssetKey(["customers"]),
                        "upstream_column_name": "customer_lifetime_value",
                    }
                ],
            }
        ),
    }
    if asset_key_selection:
        expected_lineage_metadata_by_asset_key = {
            asset_key: lineage_metadata
            for asset_key, lineage_metadata in expected_lineage_metadata_by_asset_key.items()
            if asset_key == asset_key_selection
        }

    assert lineage_metadata_by_asset_key == expected_lineage_metadata_by_asset_key


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
