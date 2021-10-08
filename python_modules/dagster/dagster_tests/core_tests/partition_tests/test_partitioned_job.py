import pytest
from dagster import daily_partitioned_config, job, op, static_partitioned_config
from dagster.seven.compat.pendulum import create_pendulum_time


@op
def my_op(context):
    context.log.info(context.op_config)


RUN_CONFIG = {"ops": {"my_op": {"config": "hello"}}}


def test_static_partitioned_job():
    partitioned_config = static_partitioned_config(
        ["blah"],
        run_config_for_partition_fn=lambda _partition: RUN_CONFIG,
    )

    @job(config=partitioned_config)
    def my_job():
        my_op()

    all_partitions = partitioned_config.get_partitions()
    assert len(all_partitions) == 1

    blah_partition = partitioned_config.get_partition("blah")
    assert blah_partition.name == "blah"
    assert blah_partition.value == "blah"

    result = my_job.execute_in_process(partition_name="blah")
    assert result.success

    # TODO create custom exception type
    with pytest.raises(Exception, match="no matching partition named `doesnotexist`"):
        result = my_job.execute_in_process(partition_name="doesnotexist")


def test_time_based_partitioned_job():
    @daily_partitioned_config(start_date="2021-05-05")
    def partitioned_config(_start, _end):
        return RUN_CONFIG

    @job(config=partitioned_config)
    def my_job():
        my_op()

    freeze_datetime = create_pendulum_time(
        year=2021, month=5, day=6, hour=23, minute=59, second=59, tz="UTC"
    )
    all_partitions = partitioned_config.get_partitions(freeze_datetime)
    assert len(all_partitions) == 1

    partition = all_partitions[0]

    result = my_job.execute_in_process(partition_name=partition.name)
    assert result.success

    # TODO create custom exception type
    with pytest.raises(Exception, match="no matching partition named `doesnotexist`"):
        result = my_job.execute_in_process(partition_name="doesnotexist")
