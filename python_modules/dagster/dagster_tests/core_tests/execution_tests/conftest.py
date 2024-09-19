import tempfile

import pytest
from dagster._core.test_utils import instance_for_test

CUSTOM_SLEEP_INTERVAL = 3


@pytest.fixture()
def concurrency_instance():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            overrides={
                "event_log_storage": {
                    "module": "dagster.utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": temp_dir},
                },
            }
        ) as instance:
            yield instance


@pytest.fixture()
def concurrency_instance_with_default_one():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            overrides={
                "event_log_storage": {
                    "module": "dagster.utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": temp_dir},
                },
                "concurrency": {"default_op_concurrency_limit": 1},
            }
        ) as instance:
            yield instance


@pytest.fixture()
def concurrency_custom_sleep_instance():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            overrides={
                "event_log_storage": {
                    "module": "dagster.utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": temp_dir, "sleep_interval": CUSTOM_SLEEP_INTERVAL},
                },
            }
        ) as instance:
            yield instance
