import pytest
from dagster import file_relative_path
from dagster.core.instance.config import dagster_instance_config
from dagster.core.test_utils import environ


@pytest.mark.parametrize("config_filename", ("dagster.yaml", "something.yaml"))
def test_instance_yaml_config_not_set(config_filename):
    base_dir = file_relative_path(__file__, ".")
    with environ({"DAGSTER_HOME": base_dir}):
        with pytest.warns(UserWarning, match="No dagster instance configuration file"):
            dagster_instance_config(base_dir, config_filename)
