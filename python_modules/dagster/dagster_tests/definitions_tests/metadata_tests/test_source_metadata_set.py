from typing import cast

from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.metadata import (
    DEFAULT_SOURCE_FILE_KEY,
    LocalFileSource,
    SouceCodeLocationsMetadataValue,
    SourceCodeLocationsMetadataSet,
)


def test_source_metadata_set() -> None:
    source_metadata = SourceCodeLocationsMetadataSet(
        source_code_locations=SouceCodeLocationsMetadataValue(
            sources={
                DEFAULT_SOURCE_FILE_KEY: LocalFileSource(
                    file_path="/Users/dagster/Documents/my_module/assets/my_asset.py",
                    line_number=12,
                )
            }
        )
    )

    dict_source_metadata = dict(source_metadata)
    assert dict_source_metadata == {
        "dagster/source_code_locations": source_metadata.source_code_locations
    }
    source_data = cast(
        SouceCodeLocationsMetadataValue, dict_source_metadata["dagster/source_code_locations"]
    )
    assert len(source_data.sources) == 1
    assert isinstance(
        source_data.sources[DEFAULT_SOURCE_FILE_KEY],
        LocalFileSource,
    )
    AssetMaterialization(asset_key="a", metadata=dict_source_metadata)

    splat_source_metadata = {**source_metadata}
    assert splat_source_metadata == {
        "dagster/source_code_locations": source_metadata.source_code_locations
    }
    source_data = cast(
        SouceCodeLocationsMetadataValue, splat_source_metadata["dagster/source_code_locations"]
    )
    assert len(source_data.sources) == 1
    assert isinstance(
        source_data.sources[DEFAULT_SOURCE_FILE_KEY],
        LocalFileSource,
    )
    AssetMaterialization(asset_key="a", metadata=splat_source_metadata)

    assert dict(
        SourceCodeLocationsMetadataSet(source_code_locations=SouceCodeLocationsMetadataValue())
    ) == {"dagster/source_code_locations": SouceCodeLocationsMetadataValue()}
    assert SourceCodeLocationsMetadataSet.extract(
        dict(
            SourceCodeLocationsMetadataSet(source_code_locations=SouceCodeLocationsMetadataValue())
        )
    ) == SourceCodeLocationsMetadataSet(source_code_locations=SouceCodeLocationsMetadataValue())
