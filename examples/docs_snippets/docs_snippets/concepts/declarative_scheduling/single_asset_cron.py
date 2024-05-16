from dagster import SchedulingCondition
from dagster._core.definitions.declarative_scheduling.ds_asset import ds_asset as asset


@asset(scheduling_condition=SchedulingCondition.on_cron("0 0 * * *"))
def my_asset() -> None: ...
