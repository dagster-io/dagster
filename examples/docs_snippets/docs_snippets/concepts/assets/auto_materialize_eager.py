from dagster import AutoMaterializePolicy, asset


@asset
def asset1():
    ...


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def asset2(asset1):
    ...
