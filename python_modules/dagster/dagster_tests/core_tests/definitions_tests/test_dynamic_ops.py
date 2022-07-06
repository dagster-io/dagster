from dagster import op, Output, Out, job
from typing import Tuple


def test_out():
    @op(out={"out1": Out(), "out2": Out()})
    def the_op() -> Tuple[Output[str], Output[int]]:
        return (Output("4"), Output(5))

    @job
    def the_job():
        the_op()

    the_job.execute_in_process()
