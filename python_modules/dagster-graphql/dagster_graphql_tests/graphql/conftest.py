import tempfile

import pytest
from dagster.core.test_utils import instance_for_test_tempdir

from .setup import define_test_in_process_context, define_test_out_of_process_context


@pytest.yield_fixture(scope="function")
def graphql_context():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test_tempdir(
            temp_dir,
            overrides={
                "scheduler": {
                    "module": "dagster.utils.test",
                    "class": "FilesystemTestScheduler",
                    "config": {"base_dir": temp_dir},
                }
            },
        ) as instance:
            with define_test_out_of_process_context(instance) as context:
                yield context


@pytest.yield_fixture(scope="function")
def graphql_in_process_context():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test_tempdir(
            temp_dir,
            overrides={
                "scheduler": {
                    "module": "dagster.utils.test",
                    "class": "FilesystemTestScheduler",
                    "config": {"base_dir": temp_dir},
                }
            },
        ) as instance:
            yield define_test_in_process_context(instance)
