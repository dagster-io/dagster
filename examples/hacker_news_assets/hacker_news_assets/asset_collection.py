from dagster.core.asset_defs import gather_assets_from_package, AssetCollection
from . import assets

asset_collection = AssetCollection(gather_assets_from_package(assets))