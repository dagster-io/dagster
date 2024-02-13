"""Launching in EMR is prohibitively time consuming, so we just verify that the plan compiles."""
import os

from dagster import materialize_to_memory
from dagster._core.execution.api import create_execution_plan
from dagster_pyspark import PySparkResource

from with_pyspark_emr.definitions import defs, people, people_over_50


def test_emr_pyspark_execution_plan():
    os.environ["EMR_CLUSTER_ID"] = "some_cluster_id"
    create_execution_plan(defs.get_implicit_global_asset_job_def())


def test_emr_pyspark_local():
    res = materialize_to_memory(
        [people, people_over_50],
        resources={"pyspark": PySparkResource(spark_config={}), "pyspark_step_launcher": None},
    )
    assert res.success
