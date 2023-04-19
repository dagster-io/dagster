from dagster import Config, RunConfig, job, op, static_partitioned_config

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
    return RunConfig(
        ops={"continent_op": ContinentOpConfig(continent_name=partition_key)}
    )


class ContinentOpConfig(Config):
    continent_name: str


@op
def continent_op(context, config: ContinentOpConfig):
    context.log.info(config.continent_name)


@job(config=continent_config)
def continent_job():
    continent_op()
