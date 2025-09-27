from enum import Enum

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.asset_key import AssetKey


@whitelist_for_serdes
class DataQualityCheckType(Enum):
    METADATA_THRESHOLD = "METADATA_THRESHOLD"


# TODO - reconsider how we structure storing how the check should run
class DataQualityInstigator:
    pass


class OnMaterializeDataQualityInstigator(DataQualityInstigator):
    pass


class OnCronDataQualityInstigator(DataQualityInstigator):
    cron_string: str


@whitelist_for_serdes
@record
class DataQualityConfig:
    name: str
    asset_key: AssetKey
    description: str
    config: dict
    instigator: DataQualityInstigator
    check_type: DataQualityCheckType
