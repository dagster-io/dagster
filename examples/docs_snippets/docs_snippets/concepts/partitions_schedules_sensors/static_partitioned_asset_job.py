# start_job

from dagster import (
    AssetExecutionContext,
    Config,
    asset,
    define_asset_job,
    static_partitioned_config,
)

CONTINENTS = [
    "Africa",
    "Antarctica",
    "Asia",
    "Europe",
    "North America",
    "Oceania",
    "South America",
]


@static_partitioned_config(partition_keys=CONTINENTS)
def continent_config(partition_key: str):
    return {"ops": {"continents": {"config": {"continent_name": partition_key}}}}


class ContinentOpConfig(Config):
    continent_name: str


@asset
def continents(context: AssetExecutionContext, config: ContinentOpConfig):
    context.log.info(config.continent_name)


continent_job = define_asset_job(
    name="continent_job", selection=[continents], config=continent_config
)

# end_job

# start_schedule_all_partitions
from dagster import RunRequest, schedule


@schedule(cron_schedule="0 0 * * *", job=continent_job)
def continent_schedule():
    for c in CONTINENTS:
        yield RunRequest(run_key=c, partition_key=c)


# end_schedule_all_partitions

# start_single_partition
from dagster import RunRequest, schedule


@schedule(cron_schedule="0 0 * * *", job=continent_job)
def antarctica_schedule():
    return RunRequest(partition_key="Antarctica")


# end_single_partition
