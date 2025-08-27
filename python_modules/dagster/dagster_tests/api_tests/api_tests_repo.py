import string
import time

import dagster as dg
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.storage.tags import EXTERNAL_JOB_SOURCE_TAG_KEY


@dg.op
def do_something():
    return 1


@dg.op
def do_input(x):
    return x


@dg.job(name="foo")
def foo_job():
    do_input(do_something())


@dg.op
def forever_op():
    while True:
        time.sleep(10)


@dg.job(name="forever")
def forever_job():
    forever_op()


@dg.op
def do_fail():
    raise Exception("I have failed")


@dg.job
def fail_job():
    do_fail()


@dg.job(tags={EXTERNAL_JOB_SOURCE_TAG_KEY: "airflow", "foo": "bar"})
def job_with_external_tag():
    pass


baz_partitions = dg.StaticPartitionsDefinition(list(string.ascii_lowercase))

baz_config = dg.PartitionedConfig(
    partitions_def=baz_partitions,
    run_config_for_partition_key_fn=lambda key: {
        "ops": {"do_input": {"inputs": {"x": {"value": key}}}}
    },
    tags_for_partition_key_fn=lambda _partition: {"foo": "bar"},
)


@dg.job(name="baz", description="Not much tbh", partitions_def=baz_partitions, config=baz_config)
def baz_job():
    do_input()


dynamic_partitions_def = dg.DynamicPartitionsDefinition(name="dynamic_partitions")


@dg.asset(partitions_def=dynamic_partitions_def)
def dynamic_asset():
    return 1


def throw_error(_):
    raise Exception("womp womp")


def define_foo_job():
    return foo_job


@dg.job(name="other_foo")
def other_foo_job():
    do_input(do_something())


def define_other_foo_job():
    return other_foo_job


@dg.job(name="bar")
def bar_job():
    @dg.usable_as_dagster_type(name="InputTypeWithoutHydration")
    class InputTypeWithoutHydration(int):
        pass

    @dg.op(out=dg.Out(InputTypeWithoutHydration))
    def one(_):
        return 1

    @dg.op(
        ins={"some_input": dg.In(InputTypeWithoutHydration)},
        out=dg.Out(dg.Int),
    )
    def fail_subset(_, some_input):
        return some_input

    fail_subset(one())


@dg.schedule(job_name="baz", cron_schedule="* * * * *")
def partitioned_run_request_schedule():
    return dg.RunRequest(partition_key="a")


@dg.schedule(job_name="baz", cron_schedule="* * * * *")
def schedule_times_out():
    import time

    time.sleep(2)


@dg.schedule(job_name="baz", cron_schedule="* * * * *")
def schedule_error():
    raise Exception("womp womp")


def define_bar_schedules():
    return {
        "foo_schedule": dg.ScheduleDefinition(
            "foo_schedule",
            cron_schedule="* * * * *",
            job_name="foo",
            run_config={"fizz": "buzz"},
        ),
        "foo_schedule_never_execute": dg.ScheduleDefinition(
            "foo_schedule_never_execute",
            cron_schedule="* * * * *",
            job_name="foo",
            run_config={"fizz": "buzz"},
            should_execute=lambda _context: False,
        ),
        "foo_schedule_echo_time": dg.ScheduleDefinition(
            "foo_schedule_echo_time",
            cron_schedule="* * * * *",
            job_name="foo",
            run_config_fn=lambda context: {
                "passed_in_time": (
                    context.scheduled_execution_time.isoformat()
                    if context.scheduled_execution_time
                    else ""
                )
            },
        ),
        "partitioned_run_request_schedule": partitioned_run_request_schedule,
        "schedule_times_out": schedule_times_out,
        "schedule_error": schedule_error,
    }


@dg.sensor(job_name="foo")
def sensor_foo(_):
    yield dg.RunRequest(run_key=None, run_config={"foo": "FOO"}, tags={"foo": "foo_tag"})
    yield dg.RunRequest(run_key=None, run_config={"foo": "FOO"})


@dg.sensor(job_name="foo")
def sensor_times_out(_):
    import time

    time.sleep(2)


@dg.sensor(job_name="foo")
def sensor_error(_):
    raise Exception("womp womp")


@dg.sensor(job_name="foo")
def sensor_raises_dagster_error(_):
    raise dg.DagsterError("Dagster error")


@dg.job(
    metadata={"pipeline_snapshot": MetadataValue.json({"pipeline_snapshot": "pipeline_snapshot"})}
)
def pipeline_snapshot():
    do_something()
    do_fail()


@dg.repository(metadata={"string": "foo", "integer": 123})
def bar_repo():
    return {
        "jobs": {
            "bar": lambda: bar_job,
            "baz": lambda: baz_job,
            "dynamic_job": dg.define_asset_job(
                "dynamic_job", [dynamic_asset], partitions_def=dynamic_partitions_def
            ).resolve(asset_graph=AssetGraph.from_assets([dynamic_asset])),
            "fail_job": fail_job,
            "foo": foo_job,
            "forever": forever_job,
            "pipeline_snapshot": pipeline_snapshot.get_subset(op_selection=["do_something"]),
            "job_with_external_tag": job_with_external_tag,
        },
        "schedules": define_bar_schedules(),
        "sensors": {
            "sensor_foo": sensor_foo,
            "sensor_times_out": sensor_times_out,
            "sensor_error": lambda: sensor_error,
            "sensor_raises_dagster_error": lambda: sensor_raises_dagster_error,
        },
    }


@dg.repository  # pyright: ignore[reportArgumentType]
def other_repo():
    return {"jobs": {"other_foo": define_other_foo_job}}
