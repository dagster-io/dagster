from dagster import job, op
from dagster._core.definitions.partitions.partitioned_config import static_partitioned_config


@static_partitioned_config(["a", "b", "c"])
def partconf(partition):
    return {"ops": {"op1": {"letter": partition}}}


@op(config_schema={"letter": str})
def op1(): ...


@job(config=partconf)
def job_with_partition_config():
    op1()
