from dagster import AssetSpec, Definitions
from dagster._core.definitions.external_asset import external_asset_from_spec

defs = Definitions(assets=[external_asset_from_spec(AssetSpec("my_asset"))])
