import sys

from dagster import asset
from dagster._core.executor.multi_environment.execute_out_of_process import (
    execute_asset_within_inprogress_run,
)
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._serdes.serdes import deserialize_as


@asset
def one_asset() -> int:
    return 1


if __name__ == "__main__":
    run_id = sys.argv[1]
    step_key = sys.argv[2]
    ref_json = sys.argv[3]
    ref = deserialize_as(ref_json, InstanceRef)
    instance = DagsterInstance.from_ref(ref)
    execute_asset_within_inprogress_run(
        instance=instance, assets_def=one_asset, run_id=run_id, step_key=step_key
    )
