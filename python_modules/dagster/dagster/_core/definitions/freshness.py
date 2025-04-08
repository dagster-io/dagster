from enum import Enum
from typing import NamedTuple

from dagster._annotations import beta
from dagster._core.definitions.asset_key import AssetKey
from dagster._serdes import whitelist_for_serdes


@beta
@whitelist_for_serdes
class FreshnessState(str, Enum):
    PASSING = "PASSING"
    IN_VIOLATION = "IN_VIOLATION"
    NEAR_VIOLATION = "NEAR_VIOLATION"
    UNKNOWN = "UNKNOWN"


@beta
@whitelist_for_serdes
class FreshnessStateEvaluation(
    NamedTuple(
        "_FreshnessStateEvaluation",
        [
            ("asset_key", AssetKey),
            ("freshness_state", FreshnessState),
        ],
    )
):
    def __new__(cls, asset_key: AssetKey, freshness_state: FreshnessState):
        return super().__new__(cls, asset_key=asset_key, freshness_state=freshness_state)
