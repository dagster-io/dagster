import pytest
from dagster import file_relative_path
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.instance.config import dagster_instance_config
from dagster._core.run_coordinator.queued_run_coordinator import PoolGranularity
from dagster._core.test_utils import environ, instance_for_test


@pytest.mark.parametrize("config_filename", ("dagster.yaml", "something.yaml"))
def test_instance_yaml_config_not_set(config_filename, caplog):
    base_dir = file_relative_path(__file__, ".")
    with environ({"DAGSTER_HOME": base_dir}):
        dagster_instance_config(base_dir, config_filename)
        assert "No dagster instance configuration file" in caplog.text


@pytest.mark.parametrize(
    "config_filename",
    (
        "merged_run_coordinator_concurrency.yaml",
        "merged_run_queue_concurrency.yaml",
    ),
)
def test_concurrency_config(config_filename, caplog):
    base_dir = file_relative_path(__file__, "./test_config")
    with environ({"DAGSTER_HOME": base_dir}):
        instance_config, _ = dagster_instance_config(base_dir, config_filename)
        with instance_for_test(overrides=instance_config) as instance:
            run_queue_config = instance.get_run_queue_config()
            assert run_queue_config
            assert run_queue_config.max_concurrent_runs == 5
            assert run_queue_config.tag_concurrency_limits == [
                {
                    "key": "dagster/solid_selection",
                    "limit": 2,
                }
            ]
            assert run_queue_config.max_user_code_failure_retries == 3
            assert run_queue_config.user_code_failure_retry_delay == 10
            assert run_queue_config.op_concurrency_slot_buffer == 1
            assert run_queue_config.pool_granularity == PoolGranularity.RUN


@pytest.mark.parametrize(
    "config_filename",
    (
        "error_run_coordinator_concurrency_mismatch.yaml",
        "error_run_queue_concurrency_mismatch.yaml",
    ),
)
def test_concurrency_config_mismatch(config_filename, caplog):
    base_dir = file_relative_path(__file__, "./test_config")
    with environ({"DAGSTER_HOME": base_dir}):
        with pytest.raises(DagsterInvalidConfigError, match="the `concurrency > "):
            dagster_instance_config(base_dir, config_filename)
