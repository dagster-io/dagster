from dagster import Definitions, fs_io_manager
from docs_snippets.concepts.io_management.source_asset import (
    my_derived_asset,
    my_source_asset,
)


def test_source_asset():
    defs = Definitions(
        assets=[my_source_asset, my_derived_asset],
        resources={"s3_io_manager": fs_io_manager},
    )

    assert my_derived_asset([5]) == [5, 4]
