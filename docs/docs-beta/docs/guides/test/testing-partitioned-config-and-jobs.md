---
title: "Testing partitioned config and jobs"
description: Test your partition configuration and jobs.
sidebar_position: 500
---

In this article, we'll cover a few ways to test your partitioned config and jobs.

:::note

This article assumes familiarity with [partitioned assets](/guides/build/partitions-and-backfills/partitioning-assets).

:::

## Testing partitioned config

Invoking a <PyObject section="partitions" module="dagster" object="PartitionedConfig" /> object directly invokes the decorated function.

If you want to check whether the generated run config is valid for the config of a job, you can use the <PyObject section="execution" module="dagster" object="validate_run_config" /> function.

{/* TODO convert to <CodeExample> */}
```python file=/concepts/partitions_schedules_sensors/partitioned_config_test.py startafter=start_partition_config endbefore=end_partition_config
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
    # partitioned_op_job job
    assert validate_run_config(partitioned_op_job, run_config)
```

If you want to test that a <PyObject section="partitions" module="dagster" object="PartitionedConfig" /> creates the partitions you expect, use the `get_partition_keys` or `get_run_config_for_partition_key` functions:

{/* TODO convert to <CodeExample> */}
```python file=/concepts/partitions_schedules_sensors/partitioned_config_test.py startafter=start_partition_keys endbefore=end_partition_keys
from dagster import Config, OpExecutionContext


@daily_partitioned_config(start_date=datetime(2020, 1, 1), minute_offset=15)
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


class ProcessDataConfig(Config):
    start: str
    end: str


@op
def process_data(context: OpExecutionContext, config: ProcessDataConfig):
    s = config.start
    e = config.end
    context.log.info(f"processing data for {s} - {e}")


@job(config=my_offset_partitioned_config)
def do_more_stuff_partitioned():
    process_data()


def test_my_offset_partitioned_config():
    # test that the partition keys are what you expect
    keys = my_offset_partitioned_config.get_partition_keys()
    assert keys[0] == "2020-01-01"
    assert keys[1] == "2020-01-02"

    # test that the run_config for a partition is valid for partitioned_op_job
    run_config = my_offset_partitioned_config.get_run_config_for_partition_key(keys[0])
    assert validate_run_config(do_more_stuff_partitioned, run_config)

    # test that the contents of run_config are what you expect
    assert run_config == {
        "ops": {
            "process_data": {
                "config": {"start": "2020-01-01-00:15", "end": "2020-01-02-00:15"}
            }
        }
    }
```

## Testing partitioned jobs

{/* TODO fix the API docs so this can be a PyObject */}

To run a partitioned job in-process on a particular partition, supply a value for the `partition_key` argument of [`dagster.JobDefinition.execute_in_process`](/api/python-api/execution):

{/* TODO convert to <CodeExample> */}
```python file=/concepts/partitions_schedules_sensors/partitioned_job_test.py startafter=start endbefore=end
def test_partitioned_op_job():
    assert partitioned_op_job.execute_in_process(partition_key="2020-01-01").success
```
