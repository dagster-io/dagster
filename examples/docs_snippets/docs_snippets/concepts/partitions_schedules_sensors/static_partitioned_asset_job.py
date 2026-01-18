# start_job

import dagster as dg

CONTINENTS = [
    "Africa",
    "Antarctica",
    "Asia",
    "Europe",
    "North America",
    "Oceania",
    "South America",
]


@dg.static_partitioned_config(partition_keys=CONTINENTS)
def continent_config(partition_key: str):
    return {"ops": {"continents": {"config": {"continent_name": partition_key}}}}


class ContinentOpConfig(dg.Config):
    continent_name: str


@dg.asset
def continents(context: dg.AssetExecutionContext, config: ContinentOpConfig):
    context.log.info(config.continent_name)


continent_job = dg.define_asset_job(
    name="continent_job", selection=[continents], config=continent_config
)

# end_job

# start_schedule_all_partitions
import dagster as dg


@dg.schedule(cron_schedule="0 0 * * *", job=continent_job)
def continent_schedule():
    for c in CONTINENTS:
        yield dg.RunRequest(run_key=c, partition_key=c)


# end_schedule_all_partitions

# start_single_partition
import dagster as dg


@dg.schedule(cron_schedule="0 0 * * *", job=continent_job)
def antarctica_schedule():
    return dg.RunRequest(partition_key="Antarctica")


# end_single_partition
