from dagster import asset


@asset
def orders(): ...


# start

import pandas as pd

from dagster import AssetCheckResult, asset_check


@asset_check(asset=orders)
def orders_id_has_no_nulls():
    return AssetCheckResult(passed=True)


def test_orders_check():
    assert orders_id_has_no_nulls().passed


# end
