from typing import Dict, NamedTuple, Optional

import dagster._check as check
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class AssetStoreHandle(
    NamedTuple("_AssetStoreHandle", [("asset_store_key", str), ("metadata", Dict[str, object])])
):
    def __new__(cls, asset_store_key: str, metadata: Optional[Dict[str, object]] = None):
        return super(AssetStoreHandle, cls).__new__(
            cls,
            asset_store_key=check.str_param(asset_store_key, "asset_store_key"),
            metadata=check.opt_dict_param(metadata, "metadata", key_type=str),
        )
