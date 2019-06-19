import os
import uuid
import yaml

import pytest

from dagster import PipelineDefinition, execute_pipeline
from dagster.core.execution.api import create_execution_plan
from dagster.utils import script_relative_path
from dagster_spark import SparkSolidDefinition, SparkSolidError

CONFIG_FILE = '''
solids:
  spark_solid:
    inputs:
      spark_inputs: []
    config:
      spark_home: /your/spark_home
      spark_outputs: ["/tmp/dagster/events/data"]
      application_jar: "{path}"
      deploy_mode: "client"
      application_arguments: "--local-path /tmp/dagster/events/data --date 2019-01-01"
      master_url: "local[*]"
      spark_conf:
        spark:
          app:
            name: "test_app"
'''


def test_step_metadata():
    spark_solid = SparkSolidDefinition('spark_solid', main_class='something')
    pipeline = PipelineDefinition(solid_defs=[spark_solid])
    environment_dict = yaml.load(CONFIG_FILE.format(path=script_relative_path('fake.jar')))
    execution_plan = create_execution_plan(pipeline, environment_dict)

    step = execution_plan.get_step_by_key('spark_solid.compute')
    assert step.metadata == {
        'spark_submit_command': (
            '/your/spark_home/bin/spark-submit --class something '
            '--master local[*] --deploy-mode client --conf spark.app.name=test_app '
            + script_relative_path('fake.jar')
            + ' --local-path /tmp/dagster/events/data '
            '--date 2019-01-01'
        )
    }


def test_jar_not_found():
    spark_solid = SparkSolidDefinition('spark_solid', main_class='something')
    pipeline = PipelineDefinition(solid_defs=[spark_solid])
    # guid guaranteed to not exist
    environment_dict = yaml.load(CONFIG_FILE.format(path=str(uuid.uuid4())))
    with pytest.raises(
        SparkSolidError,
        match='does not exist. A valid jar must be built before running this solid.',
    ):
        execute_pipeline(pipeline, environment_dict)


NO_SPARK_HOME_CONFIG_FILE = '''
solids:
  spark_solid:
    inputs:
      spark_inputs: []
    config:
      spark_outputs: ["/tmp/dagster/events/data"]
      application_jar: "{path}"
      deploy_mode: "client"
      application_arguments: "--local-path /tmp/dagster/events/data --date 2019-01-01"
      master_url: "local[*]"
      spark_conf:
        spark:
          app:
            name: "test_app"
'''


def test_no_spark_home():
    if 'SPARK_HOME' in os.environ:
        del os.environ['SPARK_HOME']

    spark_solid = SparkSolidDefinition('spark_solid', main_class='something')
    pipeline = PipelineDefinition(solid_defs=[spark_solid])
    environment_dict = yaml.load(NO_SPARK_HOME_CONFIG_FILE.format(path=script_relative_path('.')))

    with pytest.raises(SparkSolidError) as exc_info:
        execute_pipeline(pipeline, environment_dict)

    assert str(exc_info.value) == (
        'No spark home set. You must either pass spark_home in config or set '
        '$SPARK_HOME in your environment (got None).'
    )
