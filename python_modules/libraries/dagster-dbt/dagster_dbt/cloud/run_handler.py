from collections.abc import Sequence

from dagster._annotations import preview
from dagster._record import record

from dagster_dbt.cloud.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud.types import DbtCloudJobRunStatusType, DbtCloudRun


@preview
@record
class DbtCloudJobRunHandler:
    """Handles the process of a dbt Cloud job run."""

    job_id: int
    run_id: int
    args: Sequence[str]
    client: DbtCloudWorkspaceClient

    @classmethod
    def run(
        cls, job_id: int, args: Sequence[str], client: DbtCloudWorkspaceClient
    ) -> "DbtCloudJobRunHandler":
        run_details = client.trigger_job_run(job_id, steps_override=[" ".join(["dbt", *args])])
        dbt_cloud_run = DbtCloudRun.from_run_details(run_details=run_details)
        return DbtCloudJobRunHandler(
            job_id=job_id,
            run_id=dbt_cloud_run.id,
            args=args,
            client=client,
        )

    def wait_for_success(self) -> DbtCloudJobRunStatusType:
        run_details = self.client.poll_run(run_id=self.run_id)
        dbt_cloud_run = DbtCloudRun.from_run_details(run_details=run_details)
        return dbt_cloud_run.status
