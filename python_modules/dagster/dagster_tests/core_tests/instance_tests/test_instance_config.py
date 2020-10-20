import re

import pytest
from dagster import file_relative_path
from dagster.core.instance.config import dagster_instance_config


@pytest.mark.parametrize("config_filename", ("dagster.yaml", "something.yaml"))
def test_instance_yaml_config_not_set(config_filename):
    base_dir = file_relative_path(__file__, ".")

    with pytest.warns(
        UserWarning,
        match=re.escape(
            (
                "The dagster instance configuration file ({config_filename}) "
                "is not present at {base_dir}"
            ).format(config_filename=config_filename, base_dir=base_dir)
        ),
    ):
        dagster_instance_config(base_dir, config_filename)
