import string
import time

from dagster import (
    In,
    Int,
    Out,
    ScheduleDefinition,
    SkipReason,
    job,
    op,
    repository,
    sensor,
    usable_as_dagster_type,
)
from dagster._core.definitions.partition import PartitionedConfig, StaticPartitionsDefinition


@op
def do_something():
    return 1


@op
def do_input(x):
    return x


@job(name="foo")
def foo_job():
    do_input(do_something())


baz_partitions = StaticPartitionsDefinition(list(string.ascii_lowercase))

baz_config = PartitionedConfig(
    partitions_def=baz_partitions,
    run_config_for_partition_key_fn=lambda key: {
        "ops": {"do_input": {"inputs": {"x": {"value": key}}}}
    },
    tags_for_partition_key_fn=lambda _key: {"foo": "bar"},
)


@job(name="baz", description="Not much tbh", partitions_def=baz_partitions, config=baz_config)
def baz_job():
    do_input()


def define_foo_job():
    return foo_job


@job(name="bar")
def bar_job():
    @usable_as_dagster_type(name="InputTypeWithoutHydration")
    class InputTypeWithoutHydration(int):
        pass

    @op(out=Out(InputTypeWithoutHydration))
    def one(_):
        return 1

    @op(
        ins={"some_input": In(InputTypeWithoutHydration)},
        out=Out(Int),
    )
    def fail_subset(_, some_input):
        return some_input

    fail_subset(one())


def define_bar_schedules():
    return {
        "foo_schedule": ScheduleDefinition(
            "foo_schedule",
            cron_schedule="* * * * *",
            job_name="foo",
            run_config={},
        )
    }


@sensor(job_name="bar")
def slow_sensor(_):
    time.sleep(5)
    yield SkipReason("Oops fell asleep")


def error_partition_fn():
    raise Exception("womp womp")


def error_partition_config_fn():
    raise Exception("womp womp")


def error_partition_tags_fn(_partition):
    raise Exception("womp womp")


@repository
def bar_repo():
    return {
        "jobs": {
            "foo": define_foo_job,
            "bar": lambda: bar_job,
            "baz": lambda: baz_job,
        },
        "schedules": define_bar_schedules(),
        "sensors": {
            "slow_sensor": lambda: slow_sensor,
        },
    }
