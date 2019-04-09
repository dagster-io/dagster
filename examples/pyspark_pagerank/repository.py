from dagster import RepositoryDefinition

from pipeline import define_pipeline
from steps.step_one import define_pagerank_pipeline_step_one


def define_repository():
    return RepositoryDefinition(
        name='pyspark_pagerank_repo_step_one', pipeline_dict={'pyspark_pagerank': define_pipeline}
    )

