from dagster._core.definitions.declarative_scheduling.ds_asset import ds_asset as asset
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    Scheduling,
)

daily_cron = Scheduling.on_cron("0 0 * * *")


@asset(scheduling=daily_cron)
def asset_one() -> None: ...


@asset(scheduling=daily_cron)
def asset_two() -> None: ...
