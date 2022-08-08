from dagster._legacy import pipeline

from .baz import baz_op  # pylint: disable=import-error


@pipeline
def bar_pipeline():
    baz_op()
