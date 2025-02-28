from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from dagster._annotations import preview
from dagster._record import record

if TYPE_CHECKING:
    from dagster_dbt.cloud.resources_v2 import DbtCloudClient


@preview
@record
class DbtCloudJobRun:
    """Represents a dbt Cloud job run."""

    job_id: int
    run_id: int
    args: Sequence[str]
    client: "DbtCloudClient"

    @classmethod
    def run(cls, job_id: int, args: Sequence[str], client: "DbtCloudClient") -> "DbtCloudJobRun":
        response = client.trigger_job(job_id, steps=[" ".join(["dbt", *args])])
        return DbtCloudJobRun(
            job_id=job_id, run_id=response["data"]["id"], args=args, client=client
        )

    def wait_for_success(self) -> int:
        return self.client.poll_run(self.run_id)

    def get_run_results(self) -> Mapping[str, Any]:
        return self.client.get_run_results_json(self.run_id)

    def get_manifest(self) -> Mapping[str, Any]:
        return self.client.get_run_manifest_json(self.run_id)
