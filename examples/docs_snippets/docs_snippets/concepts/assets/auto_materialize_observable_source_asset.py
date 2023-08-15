import os

from dagster import AutoMaterializePolicy, DataVersion, asset, observable_source_asset


@observable_source_asset(auto_observe_interval_minutes=1)
def source_file():
    return DataVersion(str(os.path.getmtime("source_file.csv")))


@asset(
    deps=[source_file],
    auto_materialize_policy=AutoMaterializePolicy.eager(),
)
def asset1():
    ...
