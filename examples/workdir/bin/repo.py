from dagster import repository, pipeline

from src.ops import my_op


@pipeline
def my_pipeline():
    my_op()

