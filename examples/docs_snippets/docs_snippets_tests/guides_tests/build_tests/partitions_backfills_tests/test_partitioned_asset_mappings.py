from dagster import Definitions, load_assets_from_modules
from docs_snippets.guides.build.partitions_backfills import partitioned_asset_mappings


def test_definitions():
    Definitions(assets=load_assets_from_modules([partitioned_asset_mappings]))
