from dagster import repository

from .pyspark_pagerank_pipeline import pyspark_pagerank
from .steps.step_five import pyspark_pagerank_step_five
from .steps.step_four import pyspark_pagerank_step_four
from .steps.step_one import pyspark_pagerank_step_one
from .steps.step_three import pyspark_pagerank_step_three
from .steps.step_two import pyspark_pagerank_step_two


@repository
def pyspark_pagerank_repo():
    return [
        pyspark_pagerank,
        pyspark_pagerank_step_one,
        pyspark_pagerank_step_two,
        pyspark_pagerank_step_three,
        pyspark_pagerank_step_four,
        pyspark_pagerank_step_five,
    ]
