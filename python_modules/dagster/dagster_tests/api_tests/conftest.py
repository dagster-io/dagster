import dagster as dg
import pytest


@pytest.fixture()
def instance():
    with dg.instance_for_test() as instance:
        yield instance
