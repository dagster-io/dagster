from typing import List, Optional

from dagster import Config, In, Nothing, Out, Output, op
from pydantic import Field

from ..utils import generate_materializations
from .resources import DEFAULT_POLL_INTERVAL
from .types import DbtCloudOutput


class DbtCloudRunOpConfig(Config):
    job_id: int = Field(
        description=(
            "The integer ID of the relevant dbt Cloud job. You can find this value by going to the"
            " details page of your job in the dbt Cloud UI. It will be the final number in the url,"
            " e.g.:    "
            " https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/jobs/{job_id}/"
        )
    )
    poll_interval: float = Field(
        default=DEFAULT_POLL_INTERVAL,
        description="The time (in seconds) that will be waited between successive polls.",
    )
    poll_timeout: Optional[float] = Field(
        default=None,
        description=(
            "The maximum time that will waited before this operation is timed out. By "
            "default, this will never time out."
        ),
    )
    yield_materializations: bool = Field(
        default=True,
        description=(
            "If True, materializations corresponding to the results of the dbt operation will "
            "be yielded when the op executes."
        ),
    )

    asset_key_prefix: List[str] = Field(
        default=["dbt"],
        description=(
            "If provided and yield_materializations is True, these components will be used to "
            "prefix the generated asset keys."
        ),
    )


@op(
    required_resource_keys={"dbt_cloud"},
    ins={"start_after": In(Nothing)},
    out=Out(DbtCloudOutput, description="Parsed output from running the dbt Cloud job."),
    tags={"kind": "dbt_cloud"},
)
def dbt_cloud_run_op(context, config: DbtCloudRunOpConfig):
    """Initiates a run for a dbt Cloud job, then polls until the run completes. If the job
    fails or is otherwised stopped before succeeding, a `dagster.Failure` exception will be raised,
    and this op will fail.

    It requires the use of a 'dbt_cloud' resource, which is used to connect to the dbt Cloud API.

    **Config Options:**

    job_id (int)
        The integer ID of the relevant dbt Cloud job. You can find this value by going to the details
        page of your job in the dbt Cloud UI. It will be the final number in the url, e.g.:
        ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/jobs/{job_id}/``
    poll_interval (float)
        The time (in seconds) that will be waited between successive polls. Defaults to ``10``.
    poll_timeout (float)
        The maximum time (in seconds) that will waited before this operation is timed out. By
        default, this will never time out.
    yield_materializations (bool)
        If True, materializations corresponding to the results of the dbt operation will be
        yielded when the solid executes. Defaults to ``True``.
    rasset_key_prefix (float)
        If provided and yield_materializations is True, these components will be used to "
        prefix the generated asset keys. Defaults to ["dbt"].

    **Examples:**

    .. code-block:: python

        from dagster import job
        from dagster_dbt import dbt_cloud_resource, dbt_cloud_run_op

        my_dbt_cloud_resource = dbt_cloud_resource.configured(
            {"auth_token": {"env": "DBT_CLOUD_AUTH_TOKEN"}, "account_id": 77777}
        )
        run_dbt_nightly_sync = dbt_cloud_run_op.configured(
            {"job_id": 54321}, name="run_dbt_nightly_sync"
        )

        @job(resource_defs={"dbt_cloud": my_dbt_cloud_resource})
        def dbt_cloud():
            run_dbt_nightly_sync()


    """
    dbt_output = context.resources.dbt_cloud.run_job_and_poll(
        config.job_id, poll_interval=config.poll_interval, poll_timeout=config.poll_timeout
    )
    if config.yield_materializations and "results" in dbt_output.result:
        yield from generate_materializations(dbt_output, asset_key_prefix=config.asset_key_prefix)
    yield Output(
        dbt_output,
        metadata={
            "created_at": dbt_output.run_details["created_at"],
            "started_at": dbt_output.run_details["started_at"],
            "finished_at": dbt_output.run_details["finished_at"],
            "total_duration": dbt_output.run_details["duration"],
            "run_duration": dbt_output.run_details["run_duration"],
        },
    )
