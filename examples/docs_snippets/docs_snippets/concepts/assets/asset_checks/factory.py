from typing import Any, Mapping, Sequence

from mock import MagicMock

from dagster import (
    AssetCheckResult,
    AssetChecksDefinition,
    Definitions,
    asset,
    asset_check,
)


@asset
def orders():
    ...


@asset
def items():
    ...


def make_check(
    check_blob: Mapping[str, str],
) -> AssetChecksDefinition:
    @asset_check(
        name=check_blob["name"],
        asset=check_blob["asset"],
        required_resource_keys={"db_connection"},
    )
    def _check(context):
        rows = context.resources.db_connection.execute(check_blob["sql"])
        return AssetCheckResult(passed=len(rows) == 0, metadata={"num_rows": len(rows)})

    return _check


check_blobs = [
    {
        "name": "orders_id_has_no_nulls",
        "asset": "orders",
        "sql": "select * from orders where order_id is null",
    },
    {
        "name": "items_id_has_no_nulls",
        "asset": "items",
        "sql": "select * from items where item_id is null",
    },
]

defs = Definitions(
    assets=[orders, items],
    asset_checks=[make_check(check_blob) for check_blob in check_blobs],
    resources={"db_connection": MagicMock()},
)
