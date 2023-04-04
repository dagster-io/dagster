from enum import Enum
from typing import NamedTuple, Optional

from dagster._serdes.serdes import whitelist_for_serdes


@whitelist_for_serdes
class ReadinessCheckStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@whitelist_for_serdes
class ReadinessCheckResult(NamedTuple):
    status: ReadinessCheckStatus
    message: Optional[str]

    @classmethod
    def success(cls, message: Optional[str] = None):
        """Create a successful readiness check result."""
        return cls(ReadinessCheckStatus.SUCCESS, message)

    @classmethod
    def failure(cls, message: Optional[str] = None):
        """Create a failed readiness check result."""
        return cls(ReadinessCheckStatus.FAILURE, message)


class ReadinessCheckedResource:
    def readiness_check(self) -> ReadinessCheckResult:
        raise NotImplementedError()
