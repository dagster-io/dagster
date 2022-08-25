import os
import uuid

import yaml
from dagster_spark import spark_resource
from dagster_spark.ops import create_spark_op

from dagster._legacy import ModeDefinition, execute_solid
from dagster._utils import file_relative_path

CONFIG_FILE = """
ops:
  spark_op:
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
    spark_op = create_spark_op("spark_op", main_class="something")
    # guid guaranteed to not exist
    run_config = yaml.safe_load(CONFIG_FILE.format(path=str(uuid.uuid4())))

    result = execute_solid(spark_op, run_config=run_config, raise_on_error=False, mode_def=MODE_DEF)
    assert result.failure_data
    assert (
        "does not exist. A valid jar must be built before running this op."
        in result.failure_data.error.cause.message
    )


NO_SPARK_HOME_CONFIG_FILE = """
ops:
  spark_op:
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

    spark_op = create_spark_op("spark_op", main_class="something")
    run_config = yaml.safe_load(
        NO_SPARK_HOME_CONFIG_FILE.format(path=file_relative_path(__file__, "."))
    )

    result = execute_solid(spark_op, run_config=run_config, raise_on_error=False, mode_def=MODE_DEF)
    assert result.failure_data
    assert (
        "No spark home set. You must either pass spark_home in config or set "
        "$SPARK_HOME in your environment (got None)." in result.failure_data.error.cause.message
    )
