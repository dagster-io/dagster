from collections.abc import Mapping
from enum import Enum
from typing import Any, Optional

from dagster._annotations import preview
from dagster._record import record
from dagster._serdes import whitelist_for_serdes


@preview
@record
class DbtCloudAccount:
    """Represents a dbt Cloud Account, based on data as returned from the API."""

    id: int
    name: Optional[str]

    @classmethod
    def from_account_details(cls, account_details: Mapping[str, Any]) -> "DbtCloudAccount":
        return cls(
            id=account_details["id"],
            name=account_details.get("name"),
        )


@preview
@record
class DbtCloudProject:
    """Represents a dbt Cloud Project, based on data as returned from the API."""

    id: int
    name: Optional[str]

    @classmethod
    def from_project_details(cls, project_details: Mapping[str, Any]) -> "DbtCloudProject":
        return cls(
            id=project_details["id"],
            name=project_details.get("name"),
        )


@preview
@record
class DbtCloudEnvironment:
    """Represents a dbt Cloud Environment, based on data as returned from the API."""

    id: int
    name: Optional[str]

    @classmethod
    def from_environment_details(
        cls, environment_details: Mapping[str, Any]
    ) -> "DbtCloudEnvironment":
        return cls(
            id=environment_details["id"],
            name=environment_details.get("name"),
        )


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
    url: Optional[str]

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
            url=run_details.get("href"),
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
