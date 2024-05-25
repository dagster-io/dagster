from dagster import Definitions, asset
from dagster._core.definitions.declarative_scheduling.declarative_scheduling_job import (
    DeclarativeSchedulingJob,
)
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
)


@asset
def an_asset() -> None: ...


defs = Definitions(
    jobs=[
        DeclarativeSchedulingJob(
            name="my_job",
            targets=[an_asset],  # load_assets_from_module can do a bunch of work
            default_scheduling_policy=SchedulingCondition.on_cron("0 0 * * *"),
        )
    ]
)
