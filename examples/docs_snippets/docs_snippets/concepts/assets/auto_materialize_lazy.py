from dagster import AutoMaterializePolicy, FreshnessPolicy, asset


@asset
def asset1():
    ...


@asset(
    auto_materialize_policy=AutoMaterializePolicy.lazy(),
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=24 * 60),
)
def asset2(asset1):
    ...
