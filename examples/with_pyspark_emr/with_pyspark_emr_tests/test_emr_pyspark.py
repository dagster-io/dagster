"""Launching in EMR is prohibitively time consuming, so we just verify that the plan compiles."""

import os

import dagster as dg
from dagster._core.execution.api import create_execution_plan
from dagster_pyspark import PySparkResource

from with_pyspark_emr.definitions import defs, people, people_over_50


def test_emr_pyspark_execution_plan() -> None:
    os.environ["EMR_CLUSTER_ID"] = "some_cluster_id"
    with dg.instance_for_test() as instance:
        create_execution_plan(defs.get_implicit_global_asset_job_def(), instance=instance)


def test_emr_pyspark_local() -> None:
    res = dg.materialize(
        [people, people_over_50],
        resources={"pyspark": PySparkResource(spark_config={}), "pyspark_step_launcher": None},
    )
    assert res.success
