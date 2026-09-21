from dagster import Definitions, load_assets_from_modules
from docs_snippets.guides.build.partitions_backfills import partition_mapping


def test_definitions():
    Definitions(assets=load_assets_from_modules([partition_mapping]))
