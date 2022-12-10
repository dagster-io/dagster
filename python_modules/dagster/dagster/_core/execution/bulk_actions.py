from enum import Enum

from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class BulkActionType(Enum):
    PARTITION_BACKFILL = "PARTITION_BACKFILL"
    MULTI_RUN_ASSET_ACTION = "MULTI_RUN_ASSET_ACTION"
