import pytest
from dagster import AssetMaterialization
from dagster._core.definitions.metadata.metadata_set import StorageAddressMetadataSet
from dagster._core.test_utils import raise_exception_on_warnings


@pytest.fixture(autouse=True)
def error_on_warning():
    raise_exception_on_warnings()


def test_storage_address_metadata_set_basic() -> None:
    storage_address_metadata = StorageAddressMetadataSet(storage_address="s3://bucket/key")

    dict_storage_address_metadata = dict(storage_address_metadata)
    assert dict_storage_address_metadata == {"dagster/storage_address": "s3://bucket/key"}

    splat_storage_address_metadata = {**storage_address_metadata}
    assert splat_storage_address_metadata == {"dagster/storage_address": "s3://bucket/key"}
    AssetMaterialization(asset_key="a", metadata=splat_storage_address_metadata)

    assert dict(StorageAddressMetadataSet()) == {}
    assert (
        StorageAddressMetadataSet.extract(dict(StorageAddressMetadataSet()))
        == StorageAddressMetadataSet()
    )
