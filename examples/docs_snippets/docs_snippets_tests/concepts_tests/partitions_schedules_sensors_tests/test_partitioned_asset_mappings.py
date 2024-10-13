from dagster import Definitions, load_assets_from_modules
from docs_snippets.concepts.partitions_schedules_sensors import (
    partitioned_asset_mappings,
)


def test_definitions():
    Definitions(assets=load_assets_from_modules([partitioned_asset_mappings]))
