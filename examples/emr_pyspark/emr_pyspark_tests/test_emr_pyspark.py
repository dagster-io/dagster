"""Launching in EMR is prohibitively time consuming, so we just verify that the plan compiles"""
import os

from dagster.core.execution.api import create_execution_plan

from emr_pyspark.repo import make_and_filter_data_emr, make_and_filter_data_local


def test_emr_pyspark_execution_plan():
    os.environ["EMR_CLUSTER_ID"] = "some_cluster_id"
    create_execution_plan(make_and_filter_data_emr)


def test_emr_pyspark_local():
    res = make_and_filter_data_local.execute_in_process()
    assert res.success
