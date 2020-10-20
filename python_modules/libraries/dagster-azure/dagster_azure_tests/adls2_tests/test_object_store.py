from dagster.core.storage.object_store import DEFAULT_SERIALIZATION_STRATEGY
from dagster_azure.adls2 import ADLS2ObjectStore, FakeADLS2ServiceClient
from dagster_azure.blob import FakeBlobServiceClient


def test_adls2_object_store(
    storage_account, credential, file_system, caplog
):  # pylint: disable=too-many-function-args
    adls2_fake_client = FakeADLS2ServiceClient(storage_account, credential)
    blob_fake_client = FakeBlobServiceClient(storage_account, credential)

    key = "foo"
    # Uses mock ADLS2 client
    adls2_obj_store = ADLS2ObjectStore(
        file_system, adls2_client=adls2_fake_client, blob_client=blob_fake_client
    )
    res_key = adls2_obj_store.set_object(key, True, DEFAULT_SERIALIZATION_STRATEGY)
    assert res_key == "abfss://{fs}@{account}.dfs.core.windows.net/{key}".format(
        fs=file_system, account=storage_account, key=key
    )

    adls2_obj_store.set_object(key, True, DEFAULT_SERIALIZATION_STRATEGY)
    assert "Removing existing ADLS2 key" in caplog.text

    assert adls2_obj_store.has_object(key)
    assert adls2_obj_store.get_object(key, DEFAULT_SERIALIZATION_STRATEGY)[0] is True

    # Harder to test this since it requires a fake synchronised Blob client,
    # since cp_object uses blob APIs to communicate...
    # adls2_obj_store.cp_object(key, 'bar')
    # assert adls2_obj_store.has_object('bar')

    adls2_obj_store.rm_object(key)
    assert not adls2_obj_store.has_object(key)

    assert adls2_obj_store.uri_for_key(
        key
    ) == "abfss://{fs}@{account}.dfs.core.windows.net/{key}".format(
        fs=file_system, account=storage_account, key=key
    )
