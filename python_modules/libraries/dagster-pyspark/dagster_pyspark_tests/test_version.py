from dagster_pyspark import __version__
from dagster import In, Out, op


def test_version():
    assert __version__
