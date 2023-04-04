import string
import time

from dagster import (
    DynamicPartitionsDefinition,
    Int,
    ScheduleDefinition,
    asset,
    define_asset_job,
    job,
    op,
    repository,
    schedule,
    usable_as_dagster_type,
)
from dagster._core.definitions.decorators.sensor_decorator import sensor
from dagster._core.definitions.input import In
from dagster._core.definitions.output import Out
from dagster._core.definitions.partition import (
    PartitionedConfig,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.sensor_definition import RunRequest
from dagster._core.errors import DagsterError
from dagster._core.test_utils import default_mode_def_for_test
from dagster._legacy import pipeline


@op
def do_something():
    return 1


@op
def do_input(x):
    return x


@pipeline(name="foo", mode_defs=[default_mode_def_for_test])
def foo_pipeline():
    do_input(do_something())


@op
def forever_solid():
    while True:
        time.sleep(10)


@pipeline(name="forever", mode_defs=[default_mode_def_for_test])
def forever_pipeline():
    forever_solid()


@op
def do_fail():
    raise Exception("I have failed")


@pipeline
def fail_pipeline():
    do_fail()


baz_partitions = StaticPartitionsDefinition(list(string.ascii_lowercase))

baz_config = PartitionedConfig(
    partitions_def=baz_partitions,
    run_config_for_partition_fn=lambda partition: {
        "ops": {"do_input": {"inputs": {"x": {"value": partition.value}}}}
    },
    tags_for_partition_fn=lambda _partition: {"foo": "bar"},
)


@job(name="baz", description="Not much tbh", partitions_def=baz_partitions, config=baz_config)
def baz_job():
    do_input()


dynamic_partitions_def = DynamicPartitionsDefinition(name="dynamic_partitions")


@asset(partitions_def=dynamic_partitions_def)
def dynamic_asset():
    return 1


def throw_error(_):
    raise Exception("womp womp")


def define_foo_pipeline():
    return foo_pipeline


@pipeline(name="other_foo")
def other_foo_pipeline():
    do_input(do_something())


def define_other_foo_pipeline():
    return other_foo_pipeline


@pipeline(name="bar")
def bar_pipeline():
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

    return fail_subset(one())


@schedule(job_name="baz", cron_schedule="* * * * *")
def partitioned_run_request_schedule():
    return RunRequest(partition_key="a")


def define_bar_schedules():
    return {
        "foo_schedule": ScheduleDefinition(
            "foo_schedule",
            cron_schedule="* * * * *",
            job_name="foo",
            run_config={"fizz": "buzz"},
        ),
        "foo_schedule_never_execute": ScheduleDefinition(
            "foo_schedule_never_execute",
            cron_schedule="* * * * *",
            job_name="foo",
            run_config={"fizz": "buzz"},
            should_execute=lambda _context: False,
        ),
        "foo_schedule_echo_time": ScheduleDefinition(
            "foo_schedule_echo_time",
            cron_schedule="* * * * *",
            job_name="foo",
            run_config_fn=lambda context: {
                "passed_in_time": context.scheduled_execution_time.isoformat()
                if context.scheduled_execution_time
                else ""
            },
        ),
        "partitioned_run_request_schedule": partitioned_run_request_schedule,
    }


@sensor(job_name="foo")
def sensor_foo(_):
    yield RunRequest(run_key=None, run_config={"foo": "FOO"}, tags={"foo": "foo_tag"})
    yield RunRequest(run_key=None, run_config={"foo": "FOO"})


@sensor(job_name="foo")
def sensor_error(_):
    raise Exception("womp womp")


@sensor(job_name="foo")
def sensor_raises_dagster_error(_):
    raise DagsterError("Dagster error")


@repository
def bar_repo():
    return {
        "pipelines": {
            "foo": define_foo_pipeline,
            "bar": lambda: bar_pipeline,
            "fail": fail_pipeline,
            "forever": forever_pipeline,
        },
        "jobs": {
            "baz": lambda: baz_job,
            "dynamic_job": define_asset_job(
                "dynamic_job", [dynamic_asset], partitions_def=dynamic_partitions_def
            ).resolve([dynamic_asset], []),
        },
        "schedules": define_bar_schedules(),
        "sensors": {
            "sensor_foo": sensor_foo,
            "sensor_error": lambda: sensor_error,
            "sensor_raises_dagster_error": lambda: sensor_raises_dagster_error,
        },
    }


@repository
def other_repo():
    return {"pipelines": {"other_foo": define_other_foo_pipeline}}
