from dagster_k8s.version import __version__
from dagster import Out, op


def test_version():
    assert __version__
