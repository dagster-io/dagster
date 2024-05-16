from dagster._core.definitions.declarative_scheduling.ds_asset import ds_asset as asset
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    Scheduling,
)


@asset(scheduling=Scheduling.on_cron("0 0 * * *"))
def my_asset() -> None: ...
