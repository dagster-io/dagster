from typing import List, Mapping, NamedTuple, Optional

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.events import AssetKey, MetadataValue
from dagster._serdes import whitelist_for_serdes


@experimental
@whitelist_for_serdes
class AssetCheckResult(
    NamedTuple(
        "_AssetCheckResult",
        [
            ('asset_key', Optional[AssetKey]),
            ('success', bool),
            ('metadata', List[Mapping[str, MetadataValue]]),
        ]
    )):
    def __new__(cls, asset_key, success, metadata):
        return super().__new__(
            cls,
            asset_key=check.opt_inst_param(asset_key, 'asset_key', AssetKey),
            success=check.bool_param(success, 'success'),
            metadata=check.list_param(metadata, 'metadata', of_type=dict),
        )
