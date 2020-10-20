import os

import pytest
import yaml
from dagster import ModeDefinition, execute_pipeline, pipeline
from dagster_spark import create_spark_solid, spark_resource

CONFIG = """
solids:
  first_pi:
    config:
      master_url: "local[2]"
      deploy_mode: "client"
      spark_conf:
        spark:
          app:
            name: "first_pi"
      application_jar: {jar_path}
      application_arguments: '10'

  second_pi:
    config:
      master_url: "local[2]"
      deploy_mode: "client"
      spark_conf:
        spark:
          app:
            name: "second_pi"
      application_jar: {jar_path}
      application_arguments: '10'

  third_pi:
    config:
      master_url: "local[2]"
      deploy_mode: "client"
      spark_conf:
        spark:
          app:
            name: "third_pi"
      application_jar: {jar_path}
      application_arguments: '10'
"""


@pytest.mark.skip("for local testing only, we don't have $SPARK_HOME on buildkite yet")
def test_multiple_jobs():
    @pipeline(mode_defs=[ModeDefinition(resource_defs={"spark": spark_resource})])
    def pipe():
        for solid_name in ["first_pi", "second_pi", "third_pi"]:
            create_spark_solid(solid_name, main_class="org.apache.spark.examples.SparkPi")()

    # Find SPARK_HOME to get to spark examples jar
    base_path = os.path.expandvars("${SPARK_HOME}/examples/jars/")
    jar_path = None
    for fname in os.listdir(base_path):
        if fname.startswith("spark-examples"):
            jar_path = os.path.join(base_path, fname)

    result = execute_pipeline(pipe, yaml.safe_load(CONFIG.format(jar_path=jar_path)))
    assert result.success
