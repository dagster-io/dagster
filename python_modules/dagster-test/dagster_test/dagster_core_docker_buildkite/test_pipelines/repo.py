# pylint:disable=no-member
import datetime
import math
import random
import time
from collections import defaultdict

from dagster import (
    InputDefinition,
    Int,
    Output,
    OutputDefinition,
    RetryRequested,
    String,
    lambda_solid,
    pipeline,
    repository,
    solid,
)
from dagster.core.definitions.decorators import daily_schedule, schedule
from dagster.core.test_utils import nesting_composite_pipeline


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


@pipeline
def demo_pipeline():
    count_letters(multiply_the_word())


@pipeline
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


def define_long_running_pipeline():
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

    @pipeline
    def long_running_pipeline():
        for i in range(10):
            t = long_running_task.alias('first_%d' % i)()
            post_process.alias('post_process_%d' % i)(t)

    return long_running_pipeline


def define_large_pipeline():
    return nesting_composite_pipeline(depth=1, num_children=6, name='large_pipeline')


def define_schedules():
    @daily_schedule(
        name='daily_optional_outputs',
        pipeline_name=optional_outputs.name,
        start_date=datetime.datetime(2020, 1, 1),
    )
    def daily_optional_outputs(_date):
        return {}

    @schedule(
        name='frequent_large_pipe', pipeline_name='large_pipeline', cron_schedule='*/5 * * * *',
    )
    def frequent_large_pipe(_):
        return {}

    return {
        'daily_optional_outputs': daily_optional_outputs,
        'frequent_large_pipe': frequent_large_pipe,
    }


def define_step_retry_pipeline():
    @solid
    def fail_first_time(context):
        event_records = context.instance.all_logs(context.run_id)
        for event_record in event_records:
            context.log.info(event_record.message)
            if 'Started re-execution' in event_record.message:
                return 'okay perfect'

        raise RetryRequested()

    @pipeline()
    def retry_pipeline():
        fail_first_time()

    return retry_pipeline


def define_demo_execution_repo():
    @repository
    def demo_execution_repo():
        return {
            'pipelines': {
                'large_pipeline': define_large_pipeline,
                'long_running_pipeline': define_long_running_pipeline,
                'optional_outputs': optional_outputs,
                'demo_pipeline': demo_pipeline,
                'demo_error_pipeline': demo_error_pipeline,
                'retry_pipeline': define_step_retry_pipeline,
            },
            'schedules': define_schedules(),
        }

    return demo_execution_repo
