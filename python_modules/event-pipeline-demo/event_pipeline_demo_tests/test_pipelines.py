import pytest

from dagster import execute_pipeline

from dagster.utils import load_yaml_from_globs, script_relative_path

from event_pipeline_demo.pipelines import define_event_ingest_pipeline

spark = pytest.mark.spark
'''Tests that require Spark.'''

skip = pytest.mark.skip


@skip
@spark
def test_event_pipeline():
    # config = load_yaml_from_globs(script_relative_path('../environments/default.yml'))
    # result_pipeline = execute_pipeline(define_event_ingest_pipeline(), config)
    # assert result_pipeline.success
    # To support this test, we need to do the following:
    # 1. Have CircleCI publish Scala/Spark jars when that code changes
    # 2. Ensure we have Spark available to CircleCI
    # 3. Include example / test data in this repository
    raise NotImplementedError()
