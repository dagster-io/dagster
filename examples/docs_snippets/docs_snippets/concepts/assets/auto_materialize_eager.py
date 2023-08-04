from dagster import AutoMaterializePolicy, asset


@asset
def asset1():
    ...


@asset(auto_materialize_policy=AutoMaterializePolicy.eager(), deps=[asset1])
def asset2():
    ...
