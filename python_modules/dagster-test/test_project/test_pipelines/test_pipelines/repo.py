# pylint:disable=no-member
import math
import random
import time
from collections import defaultdict

from dagster_aws.s3 import s3_plus_default_storage_defs, s3_resource
from dagster_gcp.gcs.resources import gcs_resource
from dagster_gcp.gcs.system_storage import gcs_plus_default_storage_defs

from dagster import (
    InputDefinition,
    Int,
    ModeDefinition,
    Output,
    OutputDefinition,
    RepositoryDefinition,
    String,
    default_executors,
    lambda_solid,
    pipeline,
    solid,
)


@solid(input_defs=[InputDefinition('word', String)], config={'factor': Int})
def multiply_the_word(context, word):
    return word * context.solid_config['factor']


@lambda_solid(input_defs=[InputDefinition('word')])
def count_letters(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


@lambda_solid()
def error_solid():
    raise Exception('Unusual error')


@pipeline(
    mode_defs=[
        ModeDefinition(
            system_storage_defs=s3_plus_default_storage_defs, resource_defs={'s3': s3_resource}
        )
    ]
)
def demo_pipeline():
    count_letters(multiply_the_word())


def define_demo_pipeline_celery():
    from dagster_celery import celery_executor
    from dagster_celery.executor_k8s import celery_k8s_job_executor

    @pipeline(
        mode_defs=[
            ModeDefinition(
                system_storage_defs=s3_plus_default_storage_defs,
                resource_defs={'s3': s3_resource},
                executor_defs=default_executors + [celery_executor, celery_k8s_job_executor],
            )
        ]
    )
    def demo_pipeline_celery():
        count_letters(multiply_the_word())

    return demo_pipeline_celery


@pipeline(
    mode_defs=[
        ModeDefinition(
            system_storage_defs=gcs_plus_default_storage_defs, resource_defs={'gcs': gcs_resource},
        )
    ]
)
def demo_pipeline_gcs():
    count_letters(multiply_the_word())


@pipeline(
    mode_defs=[
        ModeDefinition(
            system_storage_defs=s3_plus_default_storage_defs, resource_defs={'s3': s3_resource}
        )
    ]
)
def demo_error_pipeline():
    error_solid()


@solid(
    output_defs=[
        OutputDefinition(Int, 'out_1', is_required=False),
        OutputDefinition(Int, 'out_2', is_required=False),
        OutputDefinition(Int, 'out_3', is_required=False),
    ]
)
def foo(_):
    yield Output(1, 'out_1')


@solid
def bar(_, input_arg):
    return input_arg


@pipeline
def optional_outputs():
    foo_res = foo()
    bar.alias('first_consumer')(input_arg=foo_res.out_1)
    bar.alias('second_consumer')(input_arg=foo_res.out_2)
    bar.alias('third_consumer')(input_arg=foo_res.out_3)


def define_long_running_pipeline_celery():
    from dagster_celery import celery_executor
    from dagster_celery.executor_k8s import celery_k8s_job_executor

    @solid
    def long_running_task(context):
        iterations = 20 * 30  # 20 minutes
        for i in range(iterations):
            context.log.info(
                'task in progress [%d/100]%% complete' % math.floor(100.0 * float(i) / iterations)
            )
            time.sleep(2)
        return random.randint(0, iterations)

    @solid
    def post_process(context, input_count):
        context.log.info('received input %d' % input_count)
        iterations = 60 * 2  # 2 hours
        for i in range(iterations):
            context.log.info(
                'post-process task in progress [%d/100]%% complete'
                % math.floor(100.0 * float(i) / iterations)
            )
            time.sleep(60)

    @pipeline(
        mode_defs=[
            ModeDefinition(
                system_storage_defs=s3_plus_default_storage_defs,
                resource_defs={'s3': s3_resource},
                executor_defs=default_executors + [celery_executor, celery_k8s_job_executor],
            )
        ]
    )
    def long_running_pipeline_celery():
        for i in range(10):
            t = long_running_task.alias('first_%d' % i)()
            post_process.alias('post_process_%d' % i)(t)

    return long_running_pipeline_celery


def define_demo_execution_repo():
    from .schedules import define_schedules

    return RepositoryDefinition(
        name='demo_execution_repo',
        pipeline_dict={
            'demo_pipeline_celery': define_demo_pipeline_celery,
            'long_running_pipeline_celery': define_long_running_pipeline_celery,
        },
        pipeline_defs=[demo_pipeline, demo_pipeline_gcs, demo_error_pipeline, optional_outputs,],
        schedule_defs=define_schedules(),
    )
