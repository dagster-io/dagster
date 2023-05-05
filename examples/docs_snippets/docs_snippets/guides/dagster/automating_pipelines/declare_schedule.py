from dagster import (
    AutoMaterializePolicy,
    Definitions,
    FreshnessPolicy,
    asset,
    load_assets_from_current_module,
)


@asset
def transactions_cleaned():
    ...


@asset(
    freshness_policy=FreshnessPolicy(
        maximum_lag_minutes=9 * 24, cron_schedule="0 9 * * *"
    )
)
def sales_report(transactions_cleaned):
    ...


@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=120))
def finance_report(transactions_cleaned):
    ...


defs = Definitions(
    assets=load_assets_from_current_module(
        auto_materialize_policy=AutoMaterializePolicy.lazy(),
    )
)
