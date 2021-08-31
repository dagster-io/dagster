from dagster import RunRequest, sensor
from dagster.core.storage.pipeline_run import PipelineRunStatus, PipelineRunsFilter

from ..jobs.dbt_job import dbt_prod_job, dbt_staging_job


def _dbt_on_hn_download_finished(context):
    # This is a bit of a hacky solution. We search through the run log for any successful pipeline
    # runs of the trigger_on_name, with the requested mode, and fire off a RunRequest for each one
    # we find (taking advantage of the run_key deduplication to avoid kicking off multiple runs for
    # the same upstream run).
    #
    # This is not a recommended pattern as it can put a lot of pressure on your log database.
    runs = context.instance.get_runs(
        filters=PipelineRunsFilter(
            statuses=[PipelineRunStatus.SUCCESS], pipeline_name="download_graph"
        ),
        limit=5,
    )

    for run in runs:
        # guard against runs launched with different config schema
        date = run.run_config.get("resources", {}).get("partition_start", {}).get("config", {})
        if not date:
            continue

        # get dbt pipeline config based on run
        dbt_config = {"resources": {"run_date": {"config": date.split(" ")[0]}}}
        yield RunRequest(
            run_key=str(run.run_id), run_config=dbt_config, tags={"source_run_id": run.run_id}
        )


@sensor(job=dbt_prod_job)
def dbt_on_hn_download_finished_prod(context):
    yield from _dbt_on_hn_download_finished(context)


@sensor(job=dbt_staging_job)
def dbt_on_hn_download_finished_staging(context):
    yield from _dbt_on_hn_download_finished(context)
