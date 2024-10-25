import random
import time

from dagster import (
    AssetExecutionContext,
    Definitions,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
    in_process_executor,
    job,
    op,
)

example_partition_def = StaticPartitionsDefinition(
    partition_keys=[str(i) for i in range(1, 32)],
)


@asset(
    partitions_def=example_partition_def,
)
def partitioned_asset(context: AssetExecutionContext) -> None:
    """This asset is partitioned."""
    context.log.info("Preparing to greet the world!")
    time.sleep(10)
    context.log.info("Hello world!!")


partitioned_job_long = define_asset_job(
    name="partitioned_job_long",
    partitions_def=example_partition_def,
    selection=[partitioned_asset],
)


@op
def start() -> int:
    """This op returns a simple value."""
    return 1


@op
def unreliable(num: int) -> int:
    """This op is unreliable and will fail 50% of the time."""
    failure_rate = 0.5
    if random.random() < failure_rate:
        msg = "Failed to be reliable."
        raise Exception(msg)

    return num


@op
def end(_num: int) -> None:
    """This op does nothing."""


@job(
    executor_def=in_process_executor,
    tags={"dagster-celery/queue": "short-queue"},
)
def unreliable_job_short() -> None:
    """This job is unreliable and will fail 50% of the time."""
    end(unreliable(start()))


definitions = Definitions(
    assets=[partitioned_asset],
    jobs=[partitioned_job_long, unreliable_job_short],
    executor=in_process_executor,
)
