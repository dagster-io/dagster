import os
import sys

from dagster import RepositoryDefinition
from dagster.utils import script_relative_path

# This is needed to find production query in all cases
sys.path.insert(0, os.path.abspath(script_relative_path('.')))
# above confuses pylint
# pylint: disable=wrong-import-position, import-error
from pyspark_pagerank_pipeline import define_pipeline
from steps.step_one import define_pyspark_pagerank_step_one
from steps.step_two import define_pyspark_pagerank_step_two
from steps.step_three import define_pyspark_pagerank_step_three
from steps.step_four import define_pyspark_pagerank_step_four


def define_repository():
    return RepositoryDefinition(
        name='pyspark_pagerank_repo_step_one',
        pipeline_dict={
            'pyspark_pagerank': define_pipeline,
            'pyspark_pagerank_step_one': define_pyspark_pagerank_step_one,
            'pyspark_pagerank_step_two': define_pyspark_pagerank_step_two,
            'pyspark_pagerank_step_three': define_pyspark_pagerank_step_three,
            'pyspark_pagerank_step_four': define_pyspark_pagerank_step_four,
        },
    )
