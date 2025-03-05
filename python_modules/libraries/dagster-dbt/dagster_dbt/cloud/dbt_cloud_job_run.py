from collections.abc import Sequence

from dagster._annotations import preview
from dagster._record import record

from dagster_dbt.cloud.client import DbtCloudWorkspaceClient


@preview
@record
class DbtCloudJobRun:
    """Represents a dbt Cloud job run."""

    job_id: int
    run_id: int
    args: Sequence[str]
    client: DbtCloudWorkspaceClient

    @classmethod
    def run(
        cls, job_id: int, args: Sequence[str], client: DbtCloudWorkspaceClient
    ) -> "DbtCloudJobRun":
        response = client.trigger_job(job_id, steps=[" ".join(["dbt", *args])])
        return DbtCloudJobRun(
            job_id=job_id, run_id=response["data"]["id"], args=args, client=client
        )

    def wait_for_success(self) -> int:
        return self.client.poll_run(self.run_id)
