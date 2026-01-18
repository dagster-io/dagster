from dagster_meltano import meltano_resource, meltano_run_op

import dagster as dg


@dg.job(resource_defs={"meltano": meltano_resource})
def meltano_run_job():
    tap_done = meltano_run_op("tap-1 target-1")()
    meltano_run_op("tap-2 target-2")(tap_done)


defs = dg.Definitions(jobs=[meltano_run_job])
