import json
from typing import Any

import pytest
from dagster import (
    DagsterUnknownPartitionError,
    StaticPartitionsDefinition,
    daily_partitioned_config,
    dynamic_partitioned_config,
    job,
    op,
    static_partitioned_config,
)
from dagster._core.definitions.partition import partitioned_config
from dagster._core.definitions.run_config import RunConfig
from dagster._time import create_datetime


@op
def my_op(context):
    context.log.info(context.op_config)


RUN_CONFIG = {"ops": {"my_op": {"config": "hello"}}}


@pytest.mark.parametrize(
    "config_val", [RUN_CONFIG, RunConfig(**RUN_CONFIG)], ids=["dict", "RunConfig"]
)
def test_static_partitioned_job(config_val: Any):
    @static_partitioned_config(["blah"], tags_for_partition_key_fn=lambda key: {"foo": key})
    def my_static_partitioned_config(_partition_key: str):
        return config_val

    assert (
        my_static_partitioned_config.get_run_config_for_partition_key("")["ops"]
        == RUN_CONFIG["ops"]
    )

    @job(config=my_static_partitioned_config)
    def my_job():
        my_op()

    partition_keys = my_static_partitioned_config.get_partition_keys()
    assert partition_keys == ["blah"]

    result = my_job.execute_in_process(partition_key="blah")
    assert result.success
    assert result.dagster_run.tags["foo"] == "blah"

    with pytest.raises(DagsterUnknownPartitionError, match="Could not find a partition"):
        result = my_job.execute_in_process(partition_key="doesnotexist")


def test_time_based_partitioned_job():
    @daily_partitioned_config(
        start_date="2021-05-05",
        tags_for_partition_fn=lambda start, end: {"foo": start.strftime("%Y-%m-%d")},
    )
    def my_daily_partitioned_config(_start, _end):
        return RUN_CONFIG

    assert my_daily_partitioned_config(None, None) == RUN_CONFIG

    @job(config=my_daily_partitioned_config)
    def my_job():
        my_op()

    freeze_datetime = create_datetime(
        year=2021, month=5, day=6, hour=23, minute=59, second=59, tz="UTC"
    )
    partition_keys = my_daily_partitioned_config.get_partition_keys(freeze_datetime)
    assert len(partition_keys) == 1

    partition_key = partition_keys[0]

    result = my_job.execute_in_process(partition_key=partition_key)
    assert result.success
    assert result.dagster_run.tags["foo"] == "2021-05-05"

    with pytest.raises(DagsterUnknownPartitionError, match="Could not find a partition"):
        result = my_job.execute_in_process(partition_key="doesnotexist")


def test_general_partitioned_config():
    partitions_def = StaticPartitionsDefinition(["blah"])

    @partitioned_config(partitions_def, tags_for_partition_key_fn=lambda key: {"foo": key})
    def my_partitioned_config(_partition_key):
        return {"ops": {"my_op": {"config": _partition_key}}}

    assert my_partitioned_config("blah") == {"ops": {"my_op": {"config": "blah"}}}

    @job(config=my_partitioned_config)
    def my_job():
        my_op()

    partition_keys = my_partitioned_config.get_partition_keys()
    assert partition_keys == ["blah"]

    result = my_job.execute_in_process(partition_key="blah")
    assert result.success
    assert result.dagster_run.tags["foo"] == "blah"

    with pytest.raises(DagsterUnknownPartitionError, match="Could not find a partition"):
        result = my_job.execute_in_process(partition_key="doesnotexist")


def test_dynamic_partitioned_config():
    def partition_fn(_current_time=None):
        return ["blah"]

    @dynamic_partitioned_config(partition_fn, tags_for_partition_key_fn=lambda key: {"foo": key})
    def my_dynamic_partitioned_config(_partition_key):
        return RUN_CONFIG

    assert my_dynamic_partitioned_config("") == RUN_CONFIG

    @job(config=my_dynamic_partitioned_config)
    def my_job():
        my_op()

    partition_keys = my_dynamic_partitioned_config.get_partition_keys()
    assert partition_keys == ["blah"]

    result = my_job.execute_in_process(partition_key="blah")
    assert result.success
    assert result.dagster_run.tags["foo"] == "blah"

    with pytest.raises(DagsterUnknownPartitionError, match="Could not find a partition"):
        result = my_job.execute_in_process(partition_key="doesnotexist")


def test_dict_partitioned_config_tags():
    def partition_fn(_current_time=None):
        return ["blah"]

    @dynamic_partitioned_config(
        partition_fn, tags_for_partition_key_fn=lambda key: {"foo": {"bar": key}}
    )
    def my_dynamic_partitioned_config(_partition_key):
        return RUN_CONFIG

    assert my_dynamic_partitioned_config("") == RUN_CONFIG

    @job(config=my_dynamic_partitioned_config)
    def my_job():
        my_op()

    partition_keys = my_dynamic_partitioned_config.get_partition_keys()
    assert partition_keys == ["blah"]

    result = my_job.execute_in_process(partition_key="blah")
    assert result.success
    assert result.dagster_run.tags["foo"] == json.dumps({"bar": "blah"})
