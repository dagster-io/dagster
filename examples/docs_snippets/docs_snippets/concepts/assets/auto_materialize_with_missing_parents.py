from dagster import AutoMaterializePolicy, AutoMaterializeRule, asset

allow_missing_parents_policy = AutoMaterializePolicy.eager().without_rules(
    AutoMaterializeRule.skip_on_parent_missing(),
)


@asset(auto_materialize_policy=allow_missing_parents_policy)
def asset1(upstream1, upstream2):
    ...
