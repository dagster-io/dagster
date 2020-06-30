from collections import Counter

from dagster_aws.s3 import s3_plus_default_storage_defs, s3_resource
from dagster_celery_k8s import celery_k8s_job_executor

from dagster import InputDefinition, ModeDefinition, default_executors, pipeline, repository, solid


@solid(input_defs=[InputDefinition('word', str)], config_schema={'factor': int})
def multiply_the_word(context, word):
    return word * context.solid_config['factor']


@solid(input_defs=[InputDefinition('word')])
def count_letters(_context, word):
    return dict(Counter(word))


@pipeline(
    mode_defs=[
        ModeDefinition(
            system_storage_defs=s3_plus_default_storage_defs,
            resource_defs={'s3': s3_resource},
            executor_defs=default_executors + [celery_k8s_job_executor],
        )
    ]
)
def example_pipe():
    count_letters(multiply_the_word())


@repository
def example_repo():
    return [example_pipe]
