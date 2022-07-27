# pylint: disable=redefined-outer-name
from dagster import asset


@asset
def upstream_asset():
    return [1, 2, 3]


@asset
def downstream_asset(upstream_asset):
    return upstream_asset + [4]
