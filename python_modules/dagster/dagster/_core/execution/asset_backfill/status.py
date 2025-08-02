from collections.abc import Mapping
from enum import Enum
from typing import Optional

from dagster_shared.record import record

from dagster._core.definitions.events import AssetKey


class AssetBackfillStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    MATERIALIZED = "MATERIALIZED"
    FAILED = "FAILED"


@record(kw_only=False)
class PartitionedAssetBackfillStatus:
    asset_key: AssetKey
    num_targeted_partitions: int
    partitions_counts_by_status: Mapping[AssetBackfillStatus, int]


@record(kw_only=False)
class UnpartitionedAssetBackfillStatus:
    asset_key: AssetKey
    backfill_status: Optional[AssetBackfillStatus]
