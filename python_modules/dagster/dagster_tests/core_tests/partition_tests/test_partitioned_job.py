import pytest
from dagster import (
    DagsterUnknownPartitionError,
    daily_partitioned_config,
    dynamic_partitioned_config,
    job,
    op,
    static_partitioned_config,
)
from dagster.seven.compat.pendulum import create_pendulum_time


@op
def my_op(context):
    context.log.info(context.op_config)


RUN_CONFIG = {"ops": {"my_op": {"config": "hello"}}}


def test_static_partitioned_job():
    @static_partitioned_config(["blah"])
    def my_static_partitioned_config(_partition_key: str):
        return RUN_CONFIG

    @job(config=my_static_partitioned_config)
    def my_job():
        my_op()

    partition_keys = my_static_partitioned_config.get_partition_keys()
    assert partition_keys == ["blah"]

    result = my_job.execute_in_process(partition_key="blah")
    assert result.success

    with pytest.raises(
        DagsterUnknownPartitionError, match="Could not find a partition with key `doesnotexist`"
    ):
        result = my_job.execute_in_process(partition_key="doesnotexist")


def test_time_based_partitioned_job():
    @daily_partitioned_config(start_date="2021-05-05")
    def my_daily_partitioned_config(_start, _end):
        return RUN_CONFIG

    @job(config=my_daily_partitioned_config)
    def my_job():
        my_op()

    freeze_datetime = create_pendulum_time(
        year=2021, month=5, day=6, hour=23, minute=59, second=59, tz="UTC"
    )
    partition_keys = my_daily_partitioned_config.get_partition_keys(freeze_datetime)
    assert len(partition_keys) == 1

    partition_key = partition_keys[0]

    result = my_job.execute_in_process(partition_key=partition_key)
    assert result.success

    with pytest.raises(
        DagsterUnknownPartitionError, match="Could not find a partition with key `doesnotexist`"
    ):
        result = my_job.execute_in_process(partition_key="doesnotexist")


def test_dynamic_partitioned_config():
    def partition_fn(_current_time=None):
        return ["blah"]

    @dynamic_partitioned_config(partition_fn)
    def my_dynamic_partitioned_config(_partition_key):
        return RUN_CONFIG

    @job(config=my_dynamic_partitioned_config)
    def my_job():
        my_op()

    partition_keys = my_dynamic_partitioned_config.get_partition_keys()
    assert partition_keys == ["blah"]

    result = my_job.execute_in_process(partition_key="blah")
    assert result.success

    with pytest.raises(
        DagsterUnknownPartitionError, match="Could not find a partition with key `doesnotexist`"
    ):
        result = my_job.execute_in_process(partition_key="doesnotexist")
