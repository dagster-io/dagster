# pylint: disable=redefined-outer-name

import pytest

from dagster.core.test_utils import instance_for_test


@pytest.fixture()
def instance():
    with instance_for_test() as instance:
        yield instance
