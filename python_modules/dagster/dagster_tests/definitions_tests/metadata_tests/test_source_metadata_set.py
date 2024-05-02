from typing import cast

from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.metadata import (
    DEFAULT_SOURCE_FILE_KEY,
    CodeReferencesMetadataSet,
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)


def test_source_metadata_set() -> None:
    source_metadata = CodeReferencesMetadataSet(
        code_references=CodeReferencesMetadataValue(
            sources={
                DEFAULT_SOURCE_FILE_KEY: LocalFileCodeReference(
                    file_path="/Users/dagster/Documents/my_module/assets/my_asset.py",
                    line_number=12,
                )
            }
        )
    )

    dict_source_metadata = dict(source_metadata)
    assert dict_source_metadata == {"dagster/code_references": source_metadata.code_references}
    source_data = cast(CodeReferencesMetadataValue, dict_source_metadata["dagster/code_references"])
    assert len(source_data.sources) == 1
    assert isinstance(
        source_data.sources[DEFAULT_SOURCE_FILE_KEY],
        LocalFileCodeReference,
    )
    AssetMaterialization(asset_key="a", metadata=dict_source_metadata)

    splat_source_metadata = {**source_metadata}
    assert splat_source_metadata == {"dagster/code_references": source_metadata.code_references}
    source_data = cast(
        CodeReferencesMetadataValue, splat_source_metadata["dagster/code_references"]
    )
    assert len(source_data.sources) == 1
    assert isinstance(
        source_data.sources[DEFAULT_SOURCE_FILE_KEY],
        LocalFileCodeReference,
    )
    AssetMaterialization(asset_key="a", metadata=splat_source_metadata)

    assert dict(CodeReferencesMetadataSet(code_references=CodeReferencesMetadataValue())) == {
        "dagster/code_references": CodeReferencesMetadataValue()
    }
    assert CodeReferencesMetadataSet.extract(
        dict(CodeReferencesMetadataSet(code_references=CodeReferencesMetadataValue()))
    ) == CodeReferencesMetadataSet(code_references=CodeReferencesMetadataValue())
