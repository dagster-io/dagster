"""isort:skip_file"""


from docs_snippets.concepts.partitions_schedules_sensors.partitioned_job import (
    do_stuff_partitioned,
)


# start_partition_config
from dagster import validate_run_config, daily_partitioned_config
from datetime import datetime


@daily_partitioned_config(start_date=datetime(2020, 1, 1))
def my_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}
        }
    }


def test_my_partitioned_config():
    # assert that the decorated function returns the expected output
    run_config = my_partitioned_config(datetime(2020, 1, 3), datetime(2020, 1, 4))
    assert run_config == {
        "ops": {"process_data_for_date": {"config": {"date": "2020-01-03"}}}
    }

    # assert that the output of the decorated function is valid configuration for the
    # do_stuff_partitioned job
    assert validate_run_config(do_stuff_partitioned, run_config)


# end_partition_config

# start_partition_keys


@daily_partitioned_config(start_date=datetime(2020, 1, 1), hour_offset=3)
def my_offset_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}
        }
    }


def test_my_offset_partitioned_config():
    # test that the first partition is as expected
    partitions = my_offset_partitioned_config.partitions_def.get_partitions()
    assert str(partitions[0].value.start) == "2020-01-01T03:00:00+00:00"
    assert str(partitions[0].value.end) == "2021-01-02T03:00:00+00:00"

    # get a partition for a datetime and assert the output of my_offset_partitioned_config is valid
    # configutation for the do_stuff_partitioned_job
    partition_key = my_offset_partitioned_config().get_partition_keys(
        datetime(2020, 2, 1)
    )
    run_config = my_offset_partitioned_config().get_run_config(
        partition_key=partition_key[0]
    )
    assert validate_run_config(do_stuff_partitioned, run_config)


# end_partition_keys
