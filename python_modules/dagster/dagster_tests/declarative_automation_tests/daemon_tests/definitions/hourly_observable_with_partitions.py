import random

import dagster as dg

static_partitions1 = dg.StaticPartitionsDefinition(["x", "y", "z"])


@dg.observable_source_asset(
    automation_condition=dg.AutomationCondition.on_cron("@hourly"),
    partitions_def=static_partitions1,
)
def obs():
    return dg.ObserveResult(data_version=dg.DataVersion(str(random.random())))


@dg.asset(
    deps=[obs],
    automation_condition=dg.AutomationCondition.on_cron("@hourly"),
    partitions_def=static_partitions1,
)
def mat() -> None: ...


defs = dg.Definitions(assets=[obs, mat])
