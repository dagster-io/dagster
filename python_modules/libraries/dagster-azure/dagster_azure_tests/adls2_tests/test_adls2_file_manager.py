import uuid
from unittest import mock

from dagster import ResourceDefinition, build_op_context, configured, op
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.input import In
from dagster._core.definitions.output import Out
from dagster_azure.adls2 import (
    ADLS2FileHandle,
    ADLS2FileManager,
    ADLS2Key,
    FakeADLS2Resource,
    adls2_file_manager,
)

# For deps


def test_adls2_file_manager_write(storage_account, file_system):
    file_mock = mock.MagicMock()
    adls2_mock = mock.MagicMock()
    adls2_mock.get_file_client.return_value = file_mock
    adls2_mock.account_name = storage_account
    file_manager = ADLS2FileManager(adls2_mock, file_system, "some-key")

    foo_bytes = b"foo"

    file_handle = file_manager.write_data(foo_bytes)

    assert isinstance(file_handle, ADLS2FileHandle)

    assert file_handle.account == storage_account
    assert file_handle.file_system == file_system
    assert file_handle.key.startswith("some-key/")

    assert file_mock.upload_data.call_count == 1

    file_handle = file_manager.write_data(foo_bytes, ext="foo")

    assert isinstance(file_handle, ADLS2FileHandle)

    assert file_handle.account == storage_account
    assert file_handle.file_system == file_system
    assert file_handle.key.startswith("some-key/")
    assert file_handle.key[-4:] == ".foo"

    assert file_mock.upload_data.call_count == 2


def test_adls2_file_manager_read(storage_account, file_system):
    state = {"called": 0}
    bar_bytes = b"bar"

    class DownloadMock(mock.MagicMock):
        def readinto(self, fileobj):
            fileobj.write(bar_bytes)

    class FileMock(mock.MagicMock):
        def download_file(self):
            state["called"] += 1
            assert state["called"] == 1
            return DownloadMock(file=self)

    class ADLS2Mock(mock.MagicMock):
        def get_file_client(self, *_args, **kwargs):
            state["file_system"] = kwargs["file_system"]
            file_path = kwargs["file_path"]
            state["file_path"] = kwargs["file_path"]
            return FileMock(file_path=file_path)

    adls2_mock = ADLS2Mock()
    file_manager = ADLS2FileManager(adls2_mock, file_system, "some-key")
    file_handle = ADLS2FileHandle(storage_account, file_system, "some-key/kdjfkjdkfjkd")
    with file_manager.read(file_handle) as file_obj:
        assert file_obj.read() == bar_bytes

    assert state["file_system"] == file_handle.file_system
    assert state["file_path"] == file_handle.key

    # read again. cached
    with file_manager.read(file_handle) as file_obj:
        assert file_obj.read() == bar_bytes

    file_manager.delete_local_temp()


def create_adls2_key(run_id, step_key, output_name):
    return f"dagster/storage/{run_id}/intermediates/{step_key}/{output_name}"


def test_depends_on_adls2_resource_file_manager(storage_account, file_system):
    bar_bytes = b"bar"

    @op(
        out=Out(ADLS2FileHandle),
        required_resource_keys={"file_manager"},
    )
    def emit_file(context):
        return context.resources.file_manager.write_data(bar_bytes)

    @op(
        ins={"file_handle": In(ADLS2FileHandle)},
        required_resource_keys={"file_manager"},
    )
    def accept_file(context, file_handle):
        local_path = context.resources.file_manager.copy_handle_to_local_temp(file_handle)
        assert isinstance(local_path, str)
        assert open(local_path, "rb").read() == bar_bytes

    adls2_fake_resource = FakeADLS2Resource(account_name=storage_account)
    adls2_fake_file_manager = ADLS2FileManager(
        adls2_client=adls2_fake_resource.adls2_client,  # type: ignore
        file_system=file_system,
        prefix="some-prefix",
    )

    @job(
        resource_defs={
            "adls2": ResourceDefinition.hardcoded_resource(adls2_fake_resource),
            "file_manager": ResourceDefinition.hardcoded_resource(adls2_fake_file_manager),
        },
    )
    def adls2_file_manager_test():
        accept_file(emit_file())

    result = adls2_file_manager_test.execute_in_process(
        run_config={"resources": {"file_manager": {"config": {"adls2_file_system": file_system}}}},
    )

    assert result.success

    keys_in_bucket = set(adls2_fake_resource.adls2_client.file_systems[file_system].keys())

    assert len(keys_in_bucket) == 1

    file_key = next(iter(keys_in_bucket))
    comps = file_key.split("/")

    assert "/".join(comps[:-1]) == "some-prefix"

    assert uuid.UUID(comps[-1])


@mock.patch("dagster_azure.adls2.resources.ADLS2Resource")
@mock.patch("dagster_azure.adls2.resources.ADLS2FileManager")
def test_adls_file_manager_resource(MockADLS2FileManager, MockADLS2Resource):
    did_it_run = dict(it_ran=False)

    resource_config = {
        "storage_account": "some-storage-account",
        "credential": {
            "key": "some-key",
        },
        "adls2_file_system": "some-file-system",
        "adls2_prefix": "some-prefix",
    }

    @op(required_resource_keys={"file_manager"})
    def test_op(context):
        # test that we got back a ADLS2FileManager
        assert context.resources.file_manager == MockADLS2FileManager.return_value

        # make sure the file manager was initalized with the config we are supplying
        MockADLS2FileManager.assert_called_once_with(
            adls2_client=MockADLS2Resource.return_value.adls2_client,
            file_system=resource_config["adls2_file_system"],
            prefix=resource_config["adls2_prefix"],
        )
        MockADLS2Resource.assert_called_once_with(
            storage_account=resource_config["storage_account"],
            credential=ADLS2Key(key=resource_config["credential"]["key"]),
        )

        did_it_run["it_ran"] = True

    context = build_op_context(
        resources={"file_manager": configured(adls2_file_manager)(resource_config)},
    )
    test_op(context)
    assert did_it_run["it_ran"]


@mock.patch("dagster_azure.adls2.resources.ADLS2DefaultAzureCredential")
@mock.patch("dagster_azure.adls2.resources.ADLS2Resource")
@mock.patch("dagster_azure.adls2.resources.ADLS2FileManager")
def test_adls_file_manager_resource_defaultazurecredential(
    MockADLS2FileManager, MockADLS2Resource, MockADLS2DefaultAzureCredential
):
    did_it_run = dict(it_ran=False)

    resource_config = {
        "storage_account": "some-storage-account",
        "credential": {"DefaultAzureCredential": {"exclude_environment_credential": True}},
        "adls2_file_system": "some-file-system",
        "adls2_prefix": "some-prefix",
    }

    @op(required_resource_keys={"file_manager"})
    def test_op(context):
        # test that we got back a ADLS2FileManager
        assert context.resources.file_manager == MockADLS2FileManager.return_value

        # make sure the file manager was initalized with the config we are supplying
        MockADLS2FileManager.assert_called_once_with(
            adls2_client=MockADLS2Resource.return_value.adls2_client,
            file_system=resource_config["adls2_file_system"],
            prefix=resource_config["adls2_prefix"],
        )
        MockADLS2DefaultAzureCredential.assert_called_once_with(
            kwargs={"exclude_environment_credential": True}
        )
        MockADLS2Resource.assert_called_once_with(
            storage_account=resource_config["storage_account"],
            credential=MockADLS2DefaultAzureCredential.return_value,
        )

        did_it_run["it_ran"] = True

    context = build_op_context(
        resources={"file_manager": configured(adls2_file_manager)(resource_config)},
    )
    test_op(context)
    assert did_it_run["it_ran"]
