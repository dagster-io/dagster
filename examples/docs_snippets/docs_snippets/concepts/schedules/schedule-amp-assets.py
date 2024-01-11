# ruff: isort: skip_file

# start_asset_marker

from dagster import asset, AutoMaterializeRule, AutoMaterializePolicy, Definitions

cron_policy = AutoMaterializePolicy.eager().with_rules(
    AutoMaterializeRule.materialize_on_cron(cron_schedule="* * * * *"),
)


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def hello():
    return "hello"


@asset(deps=[hello], auto_materialize_policy=cron_policy)
def world():
    return "world"


# end_asset_marker

# begin_def_marker


defs = Definitions(
    assets=[hello, world],
)
# end_def_marker
