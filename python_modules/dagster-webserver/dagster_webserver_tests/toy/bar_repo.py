from dagster import ScheduleDefinition, job, op, repository


@op
def do_something():
    return 1


@op
def do_input(x):
    return x


@job(name="foo")
def foo_job():
    do_input(do_something())


def define_foo_job():
    return foo_job


@job(name="baz", description="Not much tbh")
def baz_job():
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
        "jobs": {"foo": foo_job, "baz": baz_job},
        "schedules": define_bar_schedules(),
    }
