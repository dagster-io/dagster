"""Launching in EMR is prohibitively time consuming, so we just verify that the plan compiles"""
import os

from dagster import execute_pipeline
from dagster.core.execution.api import create_execution_plan

from ..repo import emr_preset, my_pipeline


def test_emr_pyspark_execution_plan():
    os.environ["EMR_CLUSTER_ID"] = "some_cluster_id"
    create_execution_plan(my_pipeline, mode="emr", run_config=emr_preset.run_config)


def test_emr_pyspark_local_mode():
    res = execute_pipeline(my_pipeline, mode="local")
    assert res.success
    assert res.result_for_solid("count_people").output_value() == 1
