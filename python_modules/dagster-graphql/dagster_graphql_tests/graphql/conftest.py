import pytest

from dagster import seven
from dagster.core.instance import DagsterInstance

from .setup import define_test_context


@pytest.yield_fixture(scope="function")
def graphql_context():
    with seven.TemporaryDirectory() as temp_dir:
        with DagsterInstance.local_temp(
            temp_dir,
            overrides={
                "scheduler": {
                    "module": "dagster.utils.test",
                    "class": "FilesystemTestScheduler",
                    "config": {"base_dir": temp_dir},
                }
            },
        ) as instance:
            yield define_test_context(instance)
