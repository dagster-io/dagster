import io

from dagster_azure.adls2 import ADLS2FileCache, ADLS2FileHandle, FakeADLS2ServiceClient


def test_adls2_file_cache_file_not_present(storage_account, file_system, credential):
    fake_client = FakeADLS2ServiceClient(storage_account, credential)
    file_store = ADLS2FileCache(
        storage_account=storage_account,
        file_system=file_system,
        prefix="some-prefix",
        client=fake_client,
        overwrite=False,
    )

    assert not file_store.has_file_object("foo")


def test_adls2_file_cache_file_present(storage_account, file_system, credential):
    fake_client = FakeADLS2ServiceClient(storage_account, credential)
    file_store = ADLS2FileCache(
        storage_account=storage_account,
        file_system=file_system,
        prefix="some-prefix",
        client=fake_client,
        overwrite=False,
    )

    assert not file_store.has_file_object("foo")

    file_store.write_binary_data("foo", b"bar")

    assert file_store.has_file_object("foo")


def test_adls2_file_cache_correct_handle(storage_account, file_system, credential):
    fake_client = FakeADLS2ServiceClient(storage_account, credential)
    file_store = ADLS2FileCache(
        storage_account=storage_account,
        file_system=file_system,
        prefix="some-prefix",
        client=fake_client,
        overwrite=False,
    )

    assert isinstance(file_store.get_file_handle("foo"), ADLS2FileHandle)


def test_adls2_file_cache_write_file_object(storage_account, file_system, credential):
    fake_client = FakeADLS2ServiceClient(storage_account, credential)
    file_store = ADLS2FileCache(
        storage_account=storage_account,
        file_system=file_system,
        prefix="some-prefix",
        client=fake_client,
        overwrite=False,
    )

    stream = io.BytesIO(b"content")
    file_store.write_file_object("foo", stream)
