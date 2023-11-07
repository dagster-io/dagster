import pytest
from dagster import file_relative_path
from dagster._core.instance.config import dagster_instance_config
from dagster._core.test_utils import environ, instance_for_test


@pytest.mark.parametrize("config_filename", ("dagster.yaml", "something.yaml"))
def test_instance_yaml_config_not_set(config_filename, caplog):
    base_dir = file_relative_path(__file__, ".")
    with environ({"DAGSTER_HOME": base_dir}):
        dagster_instance_config(base_dir, config_filename)
        assert "No dagster instance configuration file" in caplog.text


def test_instance_default_values_processed():
    # fields set with a default value are processed
    with instance_for_test() as instance:
        assert instance.get_settings("auto_materialize")["max_tick_retries"] == 3


def test_instance_source_values_processed():
    # StringSource/BoolSource/etc. are processed
    with pytest.raises(
        Exception,
        match='You have attempted to fetch the environment variable "SENSORS_NUM_WORKERS" which is not set',
    ):
        with instance_for_test(
            overrides={"sensors": {"num_workers": {"env": "SENSORS_NUM_WORKERS"}}}
        ) as instance:
            pass

    with environ({"SENSORS_NUM_WORKERS": "12345"}):
        with instance_for_test(
            overrides={"sensors": {"num_workers": {"env": "SENSORS_NUM_WORKERS"}}}
        ) as instance:
            assert instance.get_settings("sensors")["num_workers"] == 12345
