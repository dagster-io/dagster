from dagster import AssetKey, SourceAsset, asset
from dagster._core.definitions.metadata import (
    LocalFileSource,
    SouceCodeLocationsMetadataValue,
    SourceCodeLocationsMetadataSet,
)

# importing this makes it show up twice when we collect everything
from .asset_subpackage.another_module_with_assets import miles_davis

assert miles_davis

elvis_presley = SourceAsset(key=AssetKey("elvis_presley"))


@asset(
    metadata={
        **SourceCodeLocationsMetadataSet(
            source_code_locations=SouceCodeLocationsMetadataValue(
                sources={"my_test_source": LocalFileSource(file_path=__file__, line_number=1)}
            )
        ),
    }
)
def chuck_berry(elvis_presley, miles_davis):
    pass
