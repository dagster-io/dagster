from __future__ import annotations
from dataclasses import dataclass
from dagster import op, Output, job


def execute_op_in_job(the_op):
    @job
    def the_job():
        the_op()

    return the_job.execute_in_process()


def test_future_annotation():

    @op
    def the_op() -> Output[int]:
        Output(1)

    assert execute_op_in_job(the_op).success
