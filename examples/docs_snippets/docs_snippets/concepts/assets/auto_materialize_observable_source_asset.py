import os

from dagster import (
    AutoMaterializePolicy,
    DataVersion,
    Definitions,
    ScheduleDefinition,
    asset,
    define_asset_job,
    observable_source_asset,
)


@observable_source_asset
def source_file():
    return DataVersion(str(os.path.getmtime("source_file.csv")))


@asset(
    non_argument_deps={"source_file"},
    auto_materialize_policy=AutoMaterializePolicy.eager(),
)
def asset1():
    ...


defs = Definitions(
    assets=[source_file, asset1],
    schedules=[
        ScheduleDefinition(
            job=define_asset_job(
                "source_file_observation_job", selection=[source_file]
            ),
            cron_schedule="* * * * *",  # every minute
        )
    ],
)
