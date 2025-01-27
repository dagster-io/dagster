from enum import Enum
from typing import Any, NamedTuple, Optional


class DagsterGraphQLClientError(Exception):
    def __init__(self, *args, body=None):
        super().__init__(*args)
        self.body = body


class ReloadRepositoryLocationStatus(Enum):
    """This enum describes the status of a GraphQL mutation to reload a Dagster repository location.

    Args:
        Enum (str): can be either `ReloadRepositoryLocationStatus.SUCCESS`
            or `ReloadRepositoryLocationStatus.FAILURE`.
    """

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ShutdownRepositoryLocationStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ReloadRepositoryLocationInfo(NamedTuple):
    """This class gives information about the result of reloading
    a Dagster repository location with a GraphQL mutation.

    Args:
        status (ReloadRepositoryLocationStatus): The status of the reload repository location mutation
        failure_type: (Optional[str], optional): the failure type if `status == ReloadRepositoryLocationStatus.FAILURE`.
          Can be one of `ReloadNotSupported`, `RepositoryLocationNotFound`, or `RepositoryLocationLoadFailure`. Defaults to None.
        message (Optional[str], optional): the failure message/reason if
          `status == ReloadRepositoryLocationStatus.FAILURE`. Defaults to None.
    """

    status: ReloadRepositoryLocationStatus
    failure_type: Optional[str] = None
    message: Optional[str] = None


class ShutdownRepositoryLocationInfo(NamedTuple):
    """This class gives information about the result of shutting down the server for
    a Dagster repository location using a GraphQL mutation.

    Args:
        status (ShutdownRepositoryLocationStatus) Whether the shutdown succeeded or failed.
        message (Optional[str], optional): the failure message/reason if
          `status == ShutdownRepositoryLocationStatus.FAILURE`. Defaults to None.
    """

    status: ShutdownRepositoryLocationStatus
    message: Optional[str] = None


class JobInfo(NamedTuple):
    repository_location_name: str
    repository_name: str
    job_name: str

    @staticmethod
    def from_node(node: dict[str, Any]) -> list["JobInfo"]:
        repo_name = node["name"]
        repo_location_name = node["location"]["name"]
        return [
            JobInfo(
                repository_location_name=repo_location_name,
                repository_name=repo_name,
                job_name=job["name"],
            )
            for job in node["pipelines"]
        ]


class InvalidOutputErrorInfo(NamedTuple):
    """This class gives information about an InvalidOutputError from submitting a pipeline for execution
    from GraphQL.

    Args:
        step_key (str): key of the step that failed
        invalid_output_name (str): the name of the invalid output from the given step
    """

    step_key: str
    invalid_output_name: str
