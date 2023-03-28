from dagster import ScheduleDefinition, repository
from dagster._core.definitions.decorators import op
from dagster._legacy import pipeline


@op
def do_something():
    return 1


@op
def do_input(x):
    return x


@pipeline(name="foo")
def foo_pipeline():
    do_input(do_something())


def define_foo_pipeline():
    return foo_pipeline


@pipeline(name="baz", description="Not much tbh")
def baz_pipeline():
    do_input()


def define_bar_schedules():
    return {
        "foo_schedule": ScheduleDefinition(
            "foo_schedule",
            cron_schedule="* * * * *",
            job_name="foo",
            run_config={},
        )
    }


@repository
def bar():
    return {
        "pipelines": {"foo": foo_pipeline, "baz": baz_pipeline},
        "schedules": define_bar_schedules(),
    }
