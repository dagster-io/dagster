from collections import Counter

from dagster import In, repository
from dagster._core.definitions.decorators import op
from dagster._core.definitions.decorators.job_decorator import job
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_celery_k8s import celery_k8s_job_executor


@op(ins={"word": In()}, config_schema={"factor": int})
def multiply_the_word(context, word):
    return word * context.op_config["factor"]


@op(ins={"word": In()})
def count_letters(_context, word):
    return dict(Counter(word))


@job(
    resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
    executor_def=celery_k8s_job_executor,
)
def example_pipe():
    count_letters(multiply_the_word())


@repository
def example_repo():
    return [example_pipe]
