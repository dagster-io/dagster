import os

from databricks.sdk import WorkspaceClient

import dagster as dg


@dg.asset(
    kinds={"databricks", "notebook"},
    description="Triggers an existing Databricks job and waits for completion.",
)
def feature_engineering(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    host = os.environ["DATABRICKS_HOST"]
    token = os.environ["DATABRICKS_TOKEN"]
    job_id = int(os.environ["DATABRICKS_JOB_ID"])

    client = WorkspaceClient(host=host, token=token)

    context.log.info(f"Triggering Databricks job {job_id}")
    run = client.jobs.run_now(job_id=job_id).result()
    run_url = f"{host}/#job/{job_id}/run/{run.run_id}"

    context.log.info(
        f"Job completed — run_id={run.run_id}, state={run.state.result_state}"
    )
    return dg.MaterializeResult(
        metadata={
            "job_id": dg.MetadataValue.text(str(job_id)),
            "run_id": dg.MetadataValue.text(str(run.run_id)),
            "run_url": dg.MetadataValue.url(run_url),
            "status": dg.MetadataValue.text(str(run.state.result_state)),
        }
    )
