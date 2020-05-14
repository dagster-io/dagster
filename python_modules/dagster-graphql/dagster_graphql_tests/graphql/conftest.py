import pytest

from dagster import seven
from dagster.core.instance import DagsterInstance

from .setup import define_test_context


@pytest.yield_fixture(scope='function')
def graphql_context():
    with seven.TemporaryDirectory() as temp_dir:
        yield define_test_context(DagsterInstance.local_temp(temp_dir))
