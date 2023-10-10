from dagster import AutoMaterializePolicy, AutoMaterializeRule, asset

wait_for_all_parents_policy = AutoMaterializePolicy.eager().with_rules(
    AutoMaterializeRule.skip_on_not_all_parents_updated()
)


@asset(auto_materialize_policy=wait_for_all_parents_policy)
def asset1(upstream1, upstream2):
    ...
