"""Launching in EMR is prohibitively time consuming, so we just verify that the plan compiles"""
import os

from dagster.core.execution.api import create_execution_plan

from ..repo import count_people_over_50_emr, count_people_over_50_local


def test_emr_pyspark_execution_plan():
    os.environ["EMR_CLUSTER_ID"] = "some_cluster_id"
    create_execution_plan(count_people_over_50_emr)


def test_emr_pyspark_local():
    res = count_people_over_50_local.execute_in_process()
    assert res.success
    assert res.result_for_node("count_people").output_value() == 1
