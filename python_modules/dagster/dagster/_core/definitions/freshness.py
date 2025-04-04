from enum import Enum
from typing import NamedTuple

from dagster._core.definitions.asset_key import AssetKey
from dagster._serdes import whitelist_for_serdes


# TODO finalize states and naming
# https://dagsterlabs.slack.com/archives/C047L6H0LF4/p1743697967200509
@whitelist_for_serdes
class FreshnessState(str, Enum):
    PASSING = "PASSING"
    IN_VIOLATION = "IN_VIOLATION"
    NEAR_VIOLATION = "NEAR_VIOLATION"
    UNKNOWN = "UNKNOWN"


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
