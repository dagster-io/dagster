from dagster import Definitions, asset
from dagster._core.definitions.declarative_scheduling.declarative_scheduling_job import (
    DeclarativeSchedulingJob,
)


@asset()
def my_asset() -> None: ...


defs = Definitions(
    jobs=[
        DeclarativeSchedulingJob.cron(
            name="daily_job", targets=[my_asset], cron_schedule="0 0 * * *"
        )
    ]
)
