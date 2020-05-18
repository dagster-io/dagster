import string

from dagster import (
    PartitionSetDefinition,
    RepositoryDefinition,
    ScheduleDefinition,
    lambda_solid,
    pipeline,
)


@lambda_solid
def do_something():
    return 1


@lambda_solid
def do_input(x):
    return x


@pipeline(name='foo')
def foo_pipeline():
    do_input(do_something())


@pipeline(name='baz', description='Not much tbh')
def baz_pipeline():
    do_input()


def define_foo_pipeline():
    return foo_pipeline


def define_bar_schedules():
    return [
        ScheduleDefinition(
            "foo_schedule",
            cron_schedule="* * * * *",
            pipeline_name="test_pipeline",
            environment_dict={},
        )
    ]


def define_baz_partitions():
    return [
        PartitionSetDefinition(
            name='baz_partitions',
            pipeline_name='baz',
            partition_fn=lambda: string.ascii_lowercase,
            environment_dict_fn_for_partition=lambda partition: {
                'solids': {'do_input': {'inputs': {'x': {'value': partition}}}}
            },
        )
    ]


def define_bar_repo():
    return RepositoryDefinition(
        'bar',
        {'foo': define_foo_pipeline, 'baz': lambda: baz_pipeline},
        schedule_defs=define_bar_schedules(),
        partition_set_defs=define_baz_partitions(),
    )
