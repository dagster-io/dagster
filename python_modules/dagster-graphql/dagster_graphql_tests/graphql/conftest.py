import tempfile

import pytest
from dagster._core.test_utils import instance_for_test

from dagster_graphql_tests.graphql.repo import define_test_out_of_process_context
from dagster_graphql_tests.graphql.repo_definitions import (
    define_definitions_test_out_of_process_context,
)


@pytest.yield_fixture(scope="function")
def graphql_context():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            temp_dir=temp_dir,
            overrides={
                "scheduler": {
                    "module": "dagster.utils.test",
                    "class": "FilesystemTestScheduler",
                    "config": {"base_dir": temp_dir},
                },
                "run_coordinator": {
                    "module": "dagster._core.run_coordinator.immediately_launch_run_coordinator",
                    "class": "ImmediatelyLaunchRunCoordinator",
                },
            },
        ) as instance:
            with define_test_out_of_process_context(instance) as context:
                yield context


@pytest.yield_fixture(scope="function")
def definitions_graphql_context():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            temp_dir=temp_dir,
            overrides={
                "scheduler": {
                    "module": "dagster.utils.test",
                    "class": "FilesystemTestScheduler",
                    "config": {"base_dir": temp_dir},
                }
            },
        ) as instance:
            with define_definitions_test_out_of_process_context(instance) as context:
                yield context
