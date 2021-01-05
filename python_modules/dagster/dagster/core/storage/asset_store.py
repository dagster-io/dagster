from collections import namedtuple

from dagster import check
from dagster.serdes import whitelist_for_serdes


@whitelist_for_serdes
class AssetStoreHandle(namedtuple("_AssetStoreHandle", "asset_store_key asset_metadata")):
    def __new__(cls, asset_store_key, asset_metadata=None):
        return super(AssetStoreHandle, cls).__new__(
            cls,
            asset_store_key=check.str_param(asset_store_key, "asset_store_key"),
            asset_metadata=check.opt_dict_param(asset_metadata, "asset_metadata", key_type=str),
        )
