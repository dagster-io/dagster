from enum import Enum
from typing import NamedTuple, Optional

from dagster._serdes.serdes import whitelist_for_serdes


@whitelist_for_serdes
class VerificationStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@whitelist_for_serdes
class VerificationResult(NamedTuple):
    status: VerificationStatus
    message: Optional[str]

    @classmethod
    def success(cls, message: Optional[str] = None):
        """Create a successful verification result.
        """
        return cls(VerificationStatus.SUCCESS, message)

    @classmethod
    def failure(cls, message: Optional[str] = None):
        """Create a failed verification result.
        """
        return cls(VerificationStatus.FAILURE, message)


class ConfigVerifiable:
    def verify_config(self) -> VerificationResult:
        raise NotImplementedError()
