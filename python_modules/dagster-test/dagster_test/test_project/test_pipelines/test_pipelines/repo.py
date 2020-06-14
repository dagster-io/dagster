# pylint:disable=no-member
import datetime
import math
import os
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
    String,
    default_executors,
    lambda_solid,
    pipeline,
    repository,
    solid,
)
from dagster.core.definitions.decorators import daily_schedule, schedule
from dagster.core.test_utils import nesting_composite_pipeline


def celery_mode_defs():
    from dagster_celery import celery_executor
    from dagster_celery.executor_k8s import celery_k8s_job_executor

    return [
        ModeDefinition(
            system_storage_defs=s3_plus_default_storage_defs,
            resource_defs={'s3': s3_resource},
            executor_defs=default_executors + [celery_executor, celery_k8s_job_executor],
        )
    ]


@solid(input_defs=[InputDefinition('word', String)], config_schema={'factor': Int})
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
    @pipeline(mode_defs=celery_mode_defs())
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

    @pipeline(mode_defs=celery_mode_defs())
    def long_running_pipeline_celery():
        for i in range(10):
            t = long_running_task.alias('first_%d' % i)()
            post_process.alias('post_process_%d' % i)(t)

    return long_running_pipeline_celery


def define_large_pipeline_celery():
    return nesting_composite_pipeline(
        depth=1, num_children=6, mode_defs=celery_mode_defs(), name='large_pipeline_celery'
    )


@solid(
    tags={
        'dagster-k8s/resource_requirements': {
            'requests': {'cpu': '250m', 'memory': '64Mi'},
            'limits': {'cpu': '500m', 'memory': '2560Mi'},
        }
    }
)
def resource_req_solid(context):
    context.log.info('running')


def define_resources_limit_pipeline_celery():
    @pipeline(mode_defs=celery_mode_defs())
    def resources_limit_pipeline_celery():
        resource_req_solid()

    return resources_limit_pipeline_celery


def define_schedules():
    @daily_schedule(
        name='daily_optional_outputs',
        pipeline_name=optional_outputs.name,
        start_date=datetime.datetime(2020, 1, 1),
    )
    def daily_optional_outputs(_date):
        return {}

    @schedule(
        name='frequent_large_pipe',
        pipeline_name='large_pipeline_celery',
        cron_schedule='*/5 * * * *',
        environment_vars={
            key: os.environ.get(key)
            for key in [
                'DAGSTER_PG_PASSWORD',
                'DAGSTER_K8S_CELERY_BROKER',
                'DAGSTER_K8S_CELERY_BACKEND',
                'DAGSTER_K8S_PIPELINE_RUN_IMAGE',
                'DAGSTER_K8S_PIPELINE_RUN_NAMESPACE',
                'DAGSTER_K8S_INSTANCE_CONFIG_MAP',
                'DAGSTER_K8S_PG_PASSWORD_SECRET',
                'DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP',
                'DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY',
                'KUBERNETES_SERVICE_HOST',
                'KUBERNETES_SERVICE_PORT',
            ]
            if key in os.environ
        },
    )
    def frequent_large_pipe(_):
        from dagster_k8s import get_celery_engine_config

        cfg = get_celery_engine_config()
        cfg['storage'] = {'s3': {'config': {'s3_bucket': 'dagster-scratch-80542c2'}}}
        return cfg

    return {
        'daily_optional_outputs': daily_optional_outputs,
        'frequent_large_pipe': frequent_large_pipe,
    }


def define_demo_execution_repo():
    @repository
    def demo_execution_repo():
        return {
            'pipelines': {
                'demo_pipeline_celery': define_demo_pipeline_celery,
                'large_pipeline_celery': define_large_pipeline_celery,
                'long_running_pipeline_celery': define_long_running_pipeline_celery,
                'optional_outputs': optional_outputs,
                'demo_pipeline': demo_pipeline,
                'demo_pipeline_gcs': demo_pipeline_gcs,
                'demo_error_pipeline': demo_error_pipeline,
                'resources_limit_pipeline_celery': define_resources_limit_pipeline_celery,
            },
            'schedules': define_schedules(),
        }

    return demo_execution_repo
