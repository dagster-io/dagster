import pytest
from dagster import file_relative_path
from dagster._core.instance.config import dagster_instance_config
from dagster._core.test_utils import environ


@pytest.mark.parametrize("config_filename", ("dagster.yaml", "something.yaml"))
def test_instance_yaml_config_not_set(config_filename, caplog):
    base_dir = file_relative_path(__file__, ".")
    with environ({"DAGSTER_HOME": base_dir}):
        dagster_instance_config(base_dir, config_filename)
        assert "No dagster instance configuration file" in caplog.text
