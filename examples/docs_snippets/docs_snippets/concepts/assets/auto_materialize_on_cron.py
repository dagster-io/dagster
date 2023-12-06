from dagster import AutoMaterializePolicy, AutoMaterializeRule, asset

materialize_on_cron_policy = AutoMaterializePolicy.eager().with_rules(
    # try to materialize this asset if it hasn't been materialized since the last cron tick
    AutoMaterializeRule.materialize_on_cron("0 9 * * *", timezone="US/Central"),
)


@asset(auto_materialize_policy=materialize_on_cron_policy)
def root_asset():
    ...
