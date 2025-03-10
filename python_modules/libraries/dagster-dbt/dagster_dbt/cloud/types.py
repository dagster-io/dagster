from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import dagster._check as check
from dagster._annotations import beta, preview
from dagster._record import record
from dagster._serdes import whitelist_for_serdes
from dagster._vendored.dateutil.parser import isoparse


@beta
class DbtCloudOutput:
    """The results of executing a dbt Cloud job, along with additional metadata produced from the
    job run.

    Note that users should not construct instances of this class directly. This class is intended
    to be constructed from the JSON output of dbt Cloud commands.

    Args:
        run_details (Dict[str, Any]): The raw dictionary data representing the run details returned
            by the dbt Cloud API. For more info, see: https://docs.getdbt.com/dbt-cloud/api-v2#operation/getRunById
        result (Dict[str, Any]): Dictionary containing dbt-reported result information
            contained in run_results.json. Some dbt commands do not produce results, and will
            therefore have result = {}.
        job_id (int): The integer ID of the dbt Cloud job
        job_name (Optional[str]): The name of the dbt Cloud job (if present in the run details)
        run_id (int): The integer ID of the run that was initiated
        docs_url (str): URL of the docs generated for this run (if it exists)
    """

    def __init__(
        self,
        run_details: Mapping[str, Any],
        result: Mapping[str, Any],
    ):
        self._run_details = check.mapping_param(run_details, "run_details", key_type=str)
        self._result = check.mapping_param(result, "result", key_type=str)

    @property
    def result(self) -> Mapping[str, Any]:
        return self._result

    @property
    def run_details(self) -> Mapping[str, Any]:
        return self._run_details

    @property
    def job_id(self) -> int:
        return self.run_details["job_id"]

    @property
    def job_name(self) -> Optional[str]:
        job = self.run_details["job"]
        return job.get("name") if job else None

    @property
    def docs_url(self) -> Optional[str]:
        job = self.run_details["job"]
        if not job or not job.get("generate_docs"):
            return None
        return f"https://cloud.getdbt.com/accounts/{self.run_details['account_id']}/runs/{self.run_id}/docs/"

    @property
    def run_id(self) -> int:
        return self.run_details["id"]

    @property
    def created_at(self) -> datetime:
        return isoparse(self.run_details["created_at"])

    @property
    def updated_at(self) -> datetime:
        return isoparse(self.run_details["updated_at"])

    @property
    def dequeued_at(self) -> datetime:
        return isoparse(self.run_details["dequeued_at"])

    @property
    def started_at(self) -> datetime:
        return isoparse(self.run_details["started_at"])

    @property
    def finished_at(self) -> datetime:
        return isoparse(self.run_details["finished_at"])


@preview
@record
class DbtCloudJob:
    """Represents a dbt Cloud job, based on data as returned from the API."""

    id: int
    account_id: Optional[int]
    project_id: Optional[int]
    environment_id: Optional[int]
    name: Optional[str]

    @classmethod
    def from_job_details(cls, job_details: Mapping[str, Any]) -> "DbtCloudJob":
        return cls(
            id=job_details["id"],
            account_id=job_details.get("account_id"),
            project_id=job_details.get("project_id"),
            environment_id=job_details.get("environment_id"),
            name=job_details.get("name"),
        )


class DbtCloudJobRunStatusType(int, Enum):
    """Enum representing each status type for a run in dbt Cloud's ontology."""

    QUEUED = 1
    STARTING = 2
    RUNNING = 3
    SUCCESS = 10
    ERROR = 20
    CANCELLED = 30


@preview
@record
class DbtCloudRun:
    """Represents a dbt Cloud run, based on data as returned from the API."""

    id: int
    trigger_id: Optional[int]
    account_id: Optional[int]
    project_id: Optional[int]
    environment_id: Optional[int]
    job_definition_id: Optional[int]
    status: Optional[DbtCloudJobRunStatusType]

    @classmethod
    def from_run_details(cls, run_details: Mapping[str, Any]) -> "DbtCloudRun":
        return cls(
            id=run_details["id"],
            trigger_id=run_details.get("trigger_id"),
            account_id=run_details.get("account_id"),
            project_id=run_details.get("project_id"),
            environment_id=run_details.get("environment_id"),
            job_definition_id=run_details.get("job_definition_id"),
            status=DbtCloudJobRunStatusType(run_details.get("status"))
            if run_details.get("status")
            else None,
        )


@preview
@whitelist_for_serdes
@record
class DbtCloudWorkspaceData:
    """Represents the data of a dbt Cloud workspace, given a project and environment."""

    project_id: int
    environment_id: int
    # The ID of the ad hoc dbt Cloud job created by Dagster.
    # This job is used to parse the dbt Cloud project.
    # This job is also used to kick off cli invocation if no job ID is specified by users.
    job_id: int
    manifest: Mapping[str, Any]
