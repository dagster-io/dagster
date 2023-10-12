from dagster import Config, job, op, static_partitioned_config, OpExecutionContext

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
    return {"ops": {"continent_op": {"config": {"continent_name": partition_key}}}}


class ContinentOpConfig(Config):
    continent_name: str


@op
def continent_op(context: OpExecutionContext, config: ContinentOpConfig):
    context.log.info(config.continent_name)


@job(config=continent_config)
def continent_job():
    continent_op()
