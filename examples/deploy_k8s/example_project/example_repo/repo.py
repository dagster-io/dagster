import os
from collections import Counter

from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_celery_k8s import celery_k8s_job_executor
from dagster_k8s import k8s_job_executor

from dagster import In, config_from_files, file_relative_path, graph, op, repository


@op(ins={"word": In(str)}, config_schema={"factor": int})
def multiply_the_word(context, word):
    return word * context.op_config["factor"]


@op(ins={"word": In(str)})
def count_letters(word):
    return dict(Counter(word))


@graph
def example_graph():
    count_letters(multiply_the_word())


step_isolated_job = example_graph.to_job(
    name="step_isolated_job",
    resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
    executor_def=k8s_job_executor,
    config=config_from_files(
        [
            file_relative_path(__file__, os.path.join("..", "run_config", "k8s.yaml")),
            file_relative_path(__file__, os.path.join("..", "run_config", "pipeline.yaml")),
        ]
    ),
)

celery_step_isolated_job = example_graph.to_job(
    name="celery_step_isolated",
    resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
    executor_def=celery_k8s_job_executor,
    config=config_from_files(
        [
            file_relative_path(__file__, os.path.join("..", "run_config", "celery_k8s.yaml")),
            file_relative_path(__file__, os.path.join("..", "run_config", "pipeline.yaml")),
        ]
    ),
)

single_pod_job = example_graph.to_job(
    name="single_pod_job",
    config=config_from_files(
        [
            file_relative_path(__file__, os.path.join("..", "run_config", "pipeline.yaml")),
        ]
    ),
)


@repository
def example_repo():
    return [single_pod_job, step_isolated_job, celery_step_isolated_job]
