import pytest

import dagster as dg


@pytest.fixture()
def instance():
    with dg.instance_for_test() as instance:
        yield instance
