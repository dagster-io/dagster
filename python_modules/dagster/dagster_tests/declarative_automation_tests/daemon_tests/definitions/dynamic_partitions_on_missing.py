import dagster as dg


@dg.asset(
    partitions_def=dg.DynamicPartitionsDefinition(name="dynamic"),
    automation_condition=dg.AutomationCondition.on_missing(),
)
def A(): ...


defs = dg.Definitions(assets=[A])
