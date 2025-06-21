# ruff: isort: skip_file


from docs_snippets.concepts.partitions_schedules_sensors.partitioned_job import (
    partitioned_op_job,
)
from dagster import job, op


# start_partition_config
import dagster as dg
from datetime import datetime


@dg.daily_partitioned_config(start_date=datetime(2020, 1, 1))
def my_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}
        }
    }


# end_partition_config

# start_partition_test
import dagster as dg


def test_my_partitioned_config():
    # assert that the decorated function returns the expected output
    run_config = my_partitioned_config(datetime(2020, 1, 3), datetime(2020, 1, 4))
    assert run_config == {
        "ops": {"process_data_for_date": {"config": {"date": "2020-01-03"}}}
    }

    # assert that the output of the decorated function is valid configuration for the
    # partitioned_op_job job
    assert dg.validate_run_config(partitioned_op_job, run_config)


# end_partition_test

# start_partition_keys
import dagster as dg


@dg.daily_partitioned_config(start_date=datetime(2020, 1, 1), minute_offset=15)
def my_offset_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data": {
                "config": {
                    "start": start.strftime("%Y-%m-%d-%H:%M"),
                    "end": _end.strftime("%Y-%m-%d-%H:%M"),
                }
            }
        }
    }


class ProcessDataConfig(dg.Config):
    start: str
    end: str


@op
def process_data(context: dg.OpExecutionContext, config: ProcessDataConfig):
    s = config.start
    e = config.end
    context.log.info(f"processing data for {s} - {e}")


@job(config=my_offset_partitioned_config)
def do_more_stuff_partitioned():
    process_data()


# end_partition_keys


# start_partition_keys_test
def test_my_offset_partitioned_config():
    # test that the partition keys are what you expect
    keys = my_offset_partitioned_config.get_partition_keys()
    assert keys[0] == "2020-01-01"
    assert keys[1] == "2020-01-02"

    # test that the run_config for a partition is valid for partitioned_op_job
    run_config = my_offset_partitioned_config.get_run_config_for_partition_key(keys[0])
    assert dg.validate_run_config(do_more_stuff_partitioned, run_config)

    # test that the contents of run_config are what you expect
    assert run_config == {
        "ops": {
            "process_data": {
                "config": {"start": "2020-01-01-00:15", "end": "2020-01-02-00:15"}
            }
        }
    }


# end_partition_keys_test
