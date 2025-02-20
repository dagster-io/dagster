from collections.abc import Mapping
from unittest.mock import MagicMock

import dagster as dg


@dg.asset
def orders(): ...


@dg.asset
def items(): ...


def make_check(check_blob: Mapping[str, str]) -> dg.AssetChecksDefinition:
    @dg.asset_check(
        name=check_blob["name"],
        asset=check_blob["dg.asset"],
        required_resource_keys={"db_connection"},
    )
    def _check(context):
        rows = context.resources.db_connection.execute(check_blob["sql"])
        return dg.AssetCheckResult(
            passed=len(rows) == 0, metadata={"num_rows": len(rows)}
        )

    return _check


check_blobs = [
    {
        "name": "orders_id_has_no_nulls",
        "dg.asset": "orders",
        "sql": "select * from orders where order_id is null",
    },
    {
        "name": "items_id_has_no_nulls",
        "dg.asset": "items",
        "sql": "select * from items where item_id is null",
    },
]

defs = dg.Definitions(
    assets=[orders, items],
    asset_checks=[make_check(check_blob) for check_blob in check_blobs],
    resources={"db_connection": MagicMock()},
)
