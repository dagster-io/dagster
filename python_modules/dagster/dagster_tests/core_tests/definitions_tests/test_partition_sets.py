import datetime

import pendulum
from dagster import Partition, PartitionSetDefinition, ScheduleExecutionContext
from dagster.core.definitions.schedule import ScheduleExecutionData
from dagster.core.test_utils import instance_for_test
from dagster.seven.compat.pendulum import create_pendulum_time
from dagster.utils.partitions import date_partition_range


def test_multirun_partition_schedule_definition():
    partition_set = PartitionSetDefinition(
        name="test_time",
        pipeline_name="test_pipeline",
        partition_fn=date_partition_range(
            start=datetime.datetime(2020, 1, 5),
            end=datetime.datetime(2020, 12, 31),
            delta_range="days",
            inclusive=True,
        ),
        run_config_fn_for_partition=lambda _: {},
    )

    def _custom_partition_selector(_context, partition_set_def):
        return partition_set_def.get_partitions()[-5:]

    multi_run_schedule = partition_set.create_schedule_definition(
        "test_schedule", "* * * * *", _custom_partition_selector
    )

    with instance_for_test() as instance:
        with ScheduleExecutionContext(instance.get_ref(), pendulum.now("UTC")) as schedule_context:
            execution_data = multi_run_schedule.evaluate_tick(schedule_context)
            assert isinstance(execution_data, ScheduleExecutionData)
            assert execution_data.run_requests
            assert len(execution_data.run_requests) == 5
            assert [request.run_key for request in execution_data.run_requests] == [
                "2020-12-27",
                "2020-12-28",
                "2020-12-29",
                "2020-12-30",
                "2020-12-31",
            ]

    def _invalid_partition_selector(_cotnext, _partition_set_def):
        return [
            Partition(
                value=create_pendulum_time(year=2019, month=1, day=27, hour=1, minute=25),
                name="made_up",
            )
        ]

    invalid_schedule = partition_set.create_schedule_definition(
        "test_schedule", "* * * * *", _invalid_partition_selector
    )

    with instance_for_test() as instance:
        with ScheduleExecutionContext(instance.get_ref(), pendulum.now("UTC")) as schedule_context:
            execution_data = invalid_schedule.evaluate_tick(schedule_context)
            assert isinstance(execution_data, ScheduleExecutionData)
            assert execution_data.skip_message
            assert (
                "Partition selector returned partition not in the partition set: made_up."
                in execution_data.skip_message
            )
