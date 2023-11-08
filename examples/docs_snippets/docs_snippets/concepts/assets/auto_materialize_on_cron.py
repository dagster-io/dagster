from dagster import AutoMaterializePolicy, AutoMaterializeRule, asset

materialize_on_cron_policy = AutoMaterializePolicy.eager().with_rules(
    # try to materialize this asset if it hasn't been materialized since the last cron tick
    AutoMaterializeRule.materialize_on_cron("0 9 * * *", timezone="US/Central"),
    # to make sure assets in the middle of the graph wait for all their parents to be materialized,
    # the skip_on_not_all_parents_updated rule is added
    AutoMaterializeRule.skip_on_not_all_parents_updated(),
)


@asset(auto_materialize_policy=materialize_on_cron_policy)
def asset1(upstream1, upstream2):
    ...
