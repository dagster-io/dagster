import os
import subprocess

import pytest

from dagster import execute_pipeline

from dagster.utils import load_yaml_from_globs, script_relative_path

from event_pipeline_demo.pipelines import define_event_ingest_pipeline

spark = pytest.mark.spark
'''Tests that require Spark.'''

skip = pytest.mark.skip


# To support this test, we need to do the following:
# 1. Have CircleCI publish Scala/Spark jars when that code changes
# 2. Ensure we have Spark available to CircleCI
# 3. Include example / test data in this repository
@spark
def test_event_pipeline():
    spark_home_not_set = False

    if os.getenv('SPARK_HOME') is None:
        spark_home_not_set = True

    try:
        if spark_home_not_set:
            try:
                pyspark_show = subprocess.check_output(['pip', 'show', 'pyspark'])
            except subprocess.CalledProcessError:
                pass
            else:
                os.environ['SPARK_HOME'] = list(
                    filter(lambda x: 'Location' in x, pyspark_show.decode('utf-8').split('\n'))
                )[0].split(' ')[1]

        config = load_yaml_from_globs(script_relative_path('../environments/default.yml'))
        result_pipeline = execute_pipeline(define_event_ingest_pipeline(), config)
        assert result_pipeline.success

    finally:
        if spark_home_not_set:
            try:
                del os.environ['SPARK_HOME']
            except KeyError:
                pass
