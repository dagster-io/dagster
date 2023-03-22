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


class ConfigVerifiable:
    def verify_config(self) -> VerificationResult:
        raise NotImplementedError()
