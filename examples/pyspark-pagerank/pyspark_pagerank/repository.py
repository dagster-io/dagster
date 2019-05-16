from dagster import RepositoryDefinition

from .pyspark_pagerank_pipeline import define_pipeline
from .steps.step_one import define_pyspark_pagerank_step_one
from .steps.step_two import define_pyspark_pagerank_step_two
from .steps.step_three import define_pyspark_pagerank_step_three
from .steps.step_four import define_pyspark_pagerank_step_four
from .steps.step_five import define_pyspark_pagerank_step_five


def define_repository():
    return RepositoryDefinition.eager_construction(
        name='pyspark_pagerank_repo_step_one',
        pipelines=[
            define_pipeline(),
            define_pyspark_pagerank_step_five(),
            define_pyspark_pagerank_step_four(),
            define_pyspark_pagerank_step_one(),
            define_pyspark_pagerank_step_three(),
            define_pyspark_pagerank_step_two(),
        ],
    )
