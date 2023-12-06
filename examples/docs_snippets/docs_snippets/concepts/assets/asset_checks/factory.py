from typing import Any, Mapping, Sequence

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


def make_checks(
    check_blobs: Sequence[Mapping[str, str]],
) -> Sequence[AssetChecksDefinition]:
    checks = []
    for check_blob in check_blobs:

        @asset_check(name=check_blob["name"], asset=check_blob["asset"])
        def _check(context):
            db_connection = ...
            rows = db_connection.execute(check_blob["sql"])
            return AssetCheckResult(
                passed=len(rows) == 0, metadata={"num_rows": len(rows)}
            )

        checks.append(_check)

    return checks


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

defs = Definitions(assets=[orders, items], asset_checks=make_checks(check_blobs))
