import string
import time

from dagster import (
    InputDefinition,
    Int,
    OutputDefinition,
    PartitionSetDefinition,
    ScheduleDefinition,
    SkipReason,
    lambda_solid,
    pipeline,
    repository,
    sensor,
    solid,
    usable_as_dagster_type,
)


@lambda_solid
def do_something():
    return 1


@lambda_solid
def do_input(x):
    return x


@pipeline(name="foo")
def foo_pipeline():
    do_input(do_something())


@pipeline(name="baz", description="Not much tbh")
def baz_pipeline():
    do_input()


def define_foo_pipeline():
    return foo_pipeline


@pipeline(name="bar")
def bar_pipeline():
    @usable_as_dagster_type(name="InputTypeWithoutHydration")
    class InputTypeWithoutHydration(int):
        pass

    @solid(output_defs=[OutputDefinition(InputTypeWithoutHydration)])
    def one(_):
        return 1

    @solid(
        input_defs=[InputDefinition("some_input", InputTypeWithoutHydration)],
        output_defs=[OutputDefinition(Int)],
    )
    def fail_subset(_, some_input):
        return some_input

    return fail_subset(one())


def define_bar_schedules():
    return {
        "foo_schedule": ScheduleDefinition(
            "foo_schedule",
            cron_schedule="* * * * *",
            pipeline_name="foo",
            run_config={},
        )
    }


@sensor(pipeline_name="bar")
def slow_sensor(_):
    time.sleep(5)
    yield SkipReason("Oops fell asleep")


def error_partition_fn():
    raise Exception("womp womp")


def error_partition_config_fn():
    raise Exception("womp womp")


def error_partition_tags_fn(_partition):
    raise Exception("womp womp")


def define_baz_partitions():
    return {
        "baz_partitions": PartitionSetDefinition(
            name="baz_partitions",
            pipeline_name="baz",
            partition_fn=lambda: string.ascii_lowercase,
            run_config_fn_for_partition=lambda partition: {
                "solids": {"do_input": {"inputs": {"x": {"value": partition.value}}}}
            },
            tags_fn_for_partition=lambda _partition: {"foo": "bar"},
        ),
        "error_partitions": PartitionSetDefinition(
            name="error_partitions",
            pipeline_name="baz",
            partition_fn=error_partition_fn,
            run_config_fn_for_partition=lambda partition: {},
        ),
        "error_partition_config": PartitionSetDefinition(
            name="error_partition_config",
            pipeline_name="baz",
            partition_fn=lambda: string.ascii_lowercase,
            run_config_fn_for_partition=error_partition_config_fn,
        ),
        "error_partition_tags": PartitionSetDefinition(
            name="error_partition_tags",
            pipeline_name="baz",
            partition_fn=lambda: string.ascii_lowercase,
            run_config_fn_for_partition=lambda partition: {},
            tags_fn_for_partition=error_partition_tags_fn,
        ),
    }


@repository
def bar_repo():
    return {
        "pipelines": {
            "foo": define_foo_pipeline,
            "bar": lambda: bar_pipeline,
            "baz": lambda: baz_pipeline,
        },
        "schedules": define_bar_schedules(),
        "sensors": {
            "slow_sensor": lambda: slow_sensor,
        },
        "partition_sets": define_baz_partitions(),
    }
