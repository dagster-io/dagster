import sys

from dagster import job, op
from dagster._core.executor.multi_environment.execute_out_of_process import (
    execute_op_within_inprogress_run,
)
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._serdes.serdes import deserialize_as


@op
def returns_two() -> int:
    return 2


@job
def job_for_returns_two():
    returns_two()


if __name__ == "__main__":
    run_id = sys.argv[1]
    step_key = sys.argv[2]
    ref_json = sys.argv[3]
    ref = deserialize_as(ref_json, InstanceRef)
    instance = DagsterInstance.from_ref(ref)
    execute_op_within_inprogress_run(
        instance=instance, job_def=job_for_returns_two, run_id=run_id, step_key=step_key
    )
