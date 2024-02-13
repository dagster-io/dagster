from dagster import AutoMaterializePolicy, FreshnessPolicy, asset


@asset
def asset1():
    ...


@asset(auto_materialize_policy=AutoMaterializePolicy.lazy(), deps=[asset1])
def asset2():
    ...


@asset(
    auto_materialize_policy=AutoMaterializePolicy.lazy(),
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=24 * 60),
    deps=[asset2],
)
def asset3():
    ...
