from dagster import asset, AutoMaterializePolicy


@asset
def upstream_of_some_other():
    ...


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def some_other_asset(upstream_of_some_other):
    ...
