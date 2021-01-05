from collections import namedtuple

from dagster import check
from dagster.serdes import whitelist_for_serdes


@whitelist_for_serdes
class AssetStoreHandle(namedtuple("_AssetStoreHandle", "asset_store_key metadata")):
    def __new__(cls, asset_store_key, metadata=None):
        return super(AssetStoreHandle, cls).__new__(
            cls,
            asset_store_key=check.str_param(asset_store_key, "asset_store_key"),
            metadata=check.opt_dict_param(metadata, "metadata", key_type=str),
        )
