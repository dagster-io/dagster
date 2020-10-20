import os
import uuid

import yaml
from dagster import ModeDefinition, execute_solid
from dagster.utils import file_relative_path
from dagster_spark import create_spark_solid, spark_resource

CONFIG_FILE = """
solids:
  spark_solid:
    config:
      spark_home: /your/spark_home
      application_jar: "{path}"
      deploy_mode: "client"
      application_arguments: "--local-path /tmp/dagster/events/data --date 2019-01-01"
      master_url: "local[*]"
      spark_conf:
        spark:
          app:
            name: "test_app"
"""

MODE_DEF = ModeDefinition(resource_defs={"spark": spark_resource})


def test_jar_not_found():
    spark_solid = create_spark_solid("spark_solid", main_class="something")
    # guid guaranteed to not exist
    run_config = yaml.safe_load(CONFIG_FILE.format(path=str(uuid.uuid4())))

    result = execute_solid(
        spark_solid, run_config=run_config, raise_on_error=False, mode_def=MODE_DEF
    )
    assert result.failure_data
    assert (
        "does not exist. A valid jar must be built before running this solid."
        in result.failure_data.error.message
    )


NO_SPARK_HOME_CONFIG_FILE = """
solids:
  spark_solid:
    config:
      application_jar: "{path}"
      deploy_mode: "client"
      application_arguments: "--local-path /tmp/dagster/events/data --date 2019-01-01"
      master_url: "local[*]"
      spark_conf:
        spark:
          app:
            name: "test_app"
"""


def test_no_spark_home():
    if "SPARK_HOME" in os.environ:
        del os.environ["SPARK_HOME"]

    spark_solid = create_spark_solid("spark_solid", main_class="something")
    run_config = yaml.safe_load(
        NO_SPARK_HOME_CONFIG_FILE.format(path=file_relative_path(__file__, "."))
    )

    result = execute_solid(
        spark_solid, run_config=run_config, raise_on_error=False, mode_def=MODE_DEF
    )
    assert result.failure_data
    assert (
        "No spark home set. You must either pass spark_home in config or set "
        "$SPARK_HOME in your environment (got None)." in result.failure_data.error.message
    )
