# pylint: disable=no-value-for-parameter

from dagster import pipeline, solid


@solid
def hello_world(context):
    context.log.info('Hello World!')


@pipeline
def pyspark_pagerank_step_one():
    hello_world()
