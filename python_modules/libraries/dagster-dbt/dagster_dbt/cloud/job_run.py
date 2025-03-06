from collections.abc import Sequence

from dagster._annotations import preview
from dagster._record import record

from dagster_dbt.cloud.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud.types import DbtCloudJobRunStatusType


@preview
@record
class DbtCloudJobRun:
    """Represents a dbt Cloud job run."""

    job_id: int
    run_id: int
    args: Sequence[str]
    client: DbtCloudWorkspaceClient
    status: DbtCloudJobRunStatusType

    @classmethod
    def run(
        cls, job_id: int, args: Sequence[str], client: DbtCloudWorkspaceClient
    ) -> "DbtCloudJobRun":
        run_details = client.trigger_job(job_id, steps=[" ".join(["dbt", *args])])
        return DbtCloudJobRun(
            job_id=job_id,
            run_id=run_details["id"],
            args=args,
            client=client,
            status=DbtCloudJobRunStatusType(run_details["status"]),
        )

    def wait_for_success(self) -> DbtCloudJobRunStatusType:
        run_details = self.client.poll_run(self.run_id)
        self.status = DbtCloudJobRunStatusType(run_details["status"])
        return self.status
