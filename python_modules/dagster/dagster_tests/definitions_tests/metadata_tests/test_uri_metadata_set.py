import pytest
from dagster import AssetMaterialization
from dagster._core.definitions.metadata.metadata_set import UriMetadataSet
from dagster._core.test_utils import raise_exception_on_warnings


@pytest.fixture(autouse=True)
def error_on_warning():
    raise_exception_on_warnings()


def test_uri_metadata_set_basic() -> None:
    uri_metadata = UriMetadataSet(uri="s3://bucket/key")

    dict_uri_metadata = dict(uri_metadata)
    assert dict_uri_metadata == {"dagster/uri": "s3://bucket/key"}

    splat_uri_metadata = {**uri_metadata}
    assert splat_uri_metadata == {"dagster/uri": "s3://bucket/key"}
    AssetMaterialization(asset_key="a", metadata=splat_uri_metadata)

    assert dict(UriMetadataSet()) == {}
    assert UriMetadataSet.extract(dict(UriMetadataSet())) == UriMetadataSet()
