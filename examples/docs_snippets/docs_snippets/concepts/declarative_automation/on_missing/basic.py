import dagster as dg


@dg.asset(
    partitions_def=dg.HourlyPartitionsDefinition("2025-01-01-00:00"),
)
def upstream() -> None: ...


@dg.asset(
    deps=[upstream],
    automation_condition=dg.AutomationCondition.on_missing(),
    partitions_def=dg.DailyPartitionsDefinition("2025-01-01"),
)
def downstream() -> None: ...
