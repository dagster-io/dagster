import dagster as dg


# start_on_missing
# on_missing: materialize each weekly partition ONCE when all hourly partitions exist.
# Does NOT re-trigger if hourly partitions re-run later.
@dg.asset(
    deps=["hourly_asset"],
    partitions_def=dg.WeeklyPartitionsDefinition(start_date="2024-01-01"),
    automation_condition=dg.AutomationCondition.on_missing(),
)
def weekly_asset_on_missing(): ...


# end_on_missing


# start_eager
# eager: materialize when all hourly partitions exist, AND re-materialize whenever
# any hourly partition updates. This can produce many redundant downstream runs.
@dg.asset(
    deps=["hourly_asset"],
    partitions_def=dg.WeeklyPartitionsDefinition(start_date="2024-01-01"),
    automation_condition=dg.AutomationCondition.eager(),
)
def weekly_asset_eager(): ...


# end_eager
