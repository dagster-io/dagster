from dagster import Definitions, asset
from dagster._core.definitions.declarative_scheduling.declarative_scheduling_job import (
    DeclarativeSchedulingJob,
)


@asset
def asset_one() -> None: ...


@asset
def asset_two() -> None: ...


defs = Definitions(
    jobs=[
        DeclarativeSchedulingJob.cron(
            name="daily_job", targets=[asset_one, asset_two], cron_schedule="0 0 * * *"
        )
    ]
)
