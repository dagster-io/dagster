from dagster import SchedulingCondition
from dagster._core.definitions.declarative_scheduling.ds_asset import ds_asset as asset

daily_cron = SchedulingCondition.on_cron("0 0 * * *")


@asset(scheduling_condition=daily_cron)
def asset_one() -> None: ...


@asset(scheduling_condition=daily_cron)
def asset_two() -> None: ...
