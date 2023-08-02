import tempfile

import pytest
from click.testing import CliRunner
from dagster._cli.instance import get_concurrency, set_concurrency
from dagster._core.instance_for_test import instance_for_test


@pytest.fixture(name="instance_runner")
def mock_instance_runner():
    with tempfile.TemporaryDirectory() as dagster_home_temp:
        with instance_for_test(
            temp_dir=dagster_home_temp,
            overrides={
                "event_log_storage": {
                    "module": "dagster.utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": dagster_home_temp},
                }
            },
        ) as instance:
            runner = CliRunner(env={"DAGSTER_HOME": dagster_home_temp})
            yield instance, runner


@pytest.fixture(name="unsupported_instance_runner")
def mock_unsupported_instance_runner():
    with tempfile.TemporaryDirectory() as dagster_home_temp:
        with instance_for_test(temp_dir=dagster_home_temp) as instance:
            runner = CliRunner(env={"DAGSTER_HOME": dagster_home_temp})
            yield instance, runner


def test_get_concurrency(instance_runner):
    instance, runner = instance_runner
    result = runner.invoke(get_concurrency)
    assert result.exit_code == 1
    assert "Must either specify a key argument or" in result.output

    result = runner.invoke(get_concurrency, ["--all"])
    assert result.exit_code == 0
    assert "No concurrency limits set." in result.output

    instance.event_log_storage.set_concurrency_slots("foo", 1)
    instance.event_log_storage.set_concurrency_slots("bar", 1)

    result = runner.invoke(get_concurrency, ["foo"])
    assert result.exit_code == 0
    assert "bar" not in result.output
    assert '"foo": 0 / 1 slots occupied' in result.output

    result = runner.invoke(get_concurrency, ["--all"])
    assert result.exit_code == 0
    assert '"foo": 0 / 1 slots occupied' in result.output
    assert '"bar": 0 / 1 slots occupied' in result.output


def test_set_concurrency(instance_runner):
    instance, runner = instance_runner
    assert instance.event_log_storage.get_concurrency_info("foo").slot_count == 0
    result = runner.invoke(set_concurrency, ["foo", "1"])
    assert result.exit_code == 0
    assert "Set concurrency limit for foo to 1" in result.output


def test_unsupported(unsupported_instance_runner):
    _instance, runner = unsupported_instance_runner
    result = runner.invoke(get_concurrency)
    assert result.exit_code == 1
    assert "does not support global concurrency limits" in result.output

    result = runner.invoke(set_concurrency, ["foo", "1"])
    assert result.exit_code == 1
    assert "does not support global concurrency limits" in result.output
