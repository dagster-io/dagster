from collections.abc import Mapping
from enum import Enum
from typing import Any, Optional

from dagster._annotations import preview
from dagster._record import record
from dagster._serdes import whitelist_for_serdes


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
