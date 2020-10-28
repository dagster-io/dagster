from dagster import pipeline

from .baz import baz_solid  # pylint: disable=import-error


@pipeline
def bar_pipeline():
    baz_solid()
