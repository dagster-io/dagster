from dagster import job, op, static_partitioned_config

CONTINENTS = ["Africa", "Antarctica", "Asia", "Europe", "North America", "Oceania", "South America"]


@static_partitioned_config(partition_keys=CONTINENTS)
def continent_config(partition_key: str):
    return {"ops": {"continent_op": {"config": {"continent_name": partition_key}}}}


@op
def continent_op(context):
    context.log.info(context.op_config["continent_name"])


@job(config=continent_config)
def continent_job():
    continent_op()
