import tempfile

import dagster as dg
import pytest

CUSTOM_SLEEP_INTERVAL = 3


@pytest.fixture()
def concurrency_instance_default_granularity():
    with tempfile.TemporaryDirectory() as temp_dir:
        with dg.instance_for_test(
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
def concurrency_instance_run_granularity():
    with tempfile.TemporaryDirectory() as temp_dir:
        with dg.instance_for_test(
            overrides={
                "event_log_storage": {
                    "module": "dagster.utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": temp_dir},
                },
                "concurrency": {
                    "pools": {"granularity": "run"},
                },
            }
        ) as instance:
            yield instance


@pytest.fixture()
def concurrency_instance_op_granularity():
    with tempfile.TemporaryDirectory() as temp_dir:
        with dg.instance_for_test(
            overrides={
                "event_log_storage": {
                    "module": "dagster.utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": temp_dir},
                },
                "concurrency": {
                    "pools": {"granularity": "op"},
                },
            }
        ) as instance:
            yield instance


@pytest.fixture()
def concurrency_instance_with_default_one():
    with tempfile.TemporaryDirectory() as temp_dir:
        with dg.instance_for_test(
            overrides={
                "event_log_storage": {
                    "module": "dagster.utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": temp_dir},
                },
                "concurrency": {
                    "pools": {"granularity": "op", "default_limit": 1},
                },
            }
        ) as instance:
            yield instance


@pytest.fixture()
def concurrency_custom_sleep_instance():
    with tempfile.TemporaryDirectory() as temp_dir:
        with dg.instance_for_test(
            overrides={
                "event_log_storage": {
                    "module": "dagster.utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": temp_dir, "sleep_interval": CUSTOM_SLEEP_INTERVAL},
                },
                "concurrency": {
                    "pools": {"granularity": "op"},
                },
            }
        ) as instance:
            yield instance
