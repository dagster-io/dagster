from enum import Enum
from typing import NamedTuple, Optional


class DagsterGraphQLClientError(Exception):
    pass


class ReloadRepositoryLocationStatus(Enum):
    """This enum describes the status of a GraphQL mutation to reload a Dagster repository location

    Args:
        Enum (str): can be either `ReloadRepositoryLocationStatus.SUCCESS`
            or `ReloadRepositoryLocationStatus.FAILURE`.
    """

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ReloadRepositoryLocationInfo(NamedTuple):
    """This class gives information about the result of reloading
    a Dagster repository location with a GraphQL mutation.

    Args:
        status (ReloadRepositoryLocationStatus): The status of the reload repository location mutation
        message (Optional[str], optional): the failure message/reason if
          `status == ReloadRepositoryLocationStatus.FAILURE`. Defaults to None.
    """

    status: ReloadRepositoryLocationStatus
    message: Optional[str] = None
