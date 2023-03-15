import os
import sys
import tempfile
from unittest import mock

import pytest
from dagster import DagsterEventType, graph, op
from dagster._core.instance import DagsterInstance, InstanceRef, InstanceType
from dagster._core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster._core.run_coordinator import DefaultRunCoordinator
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.event_log import SqliteEventLogStorage
from dagster._core.storage.root import LocalArtifactStorage
from dagster._core.storage.runs import SqliteRunStorage
from dagster._core.test_utils import environ
from dagster_azure.blob import AzureBlobComputeLogManager, FakeBlobServiceClient
from dagster_tests.storage_tests.test_captured_log_manager import TestCapturedLogManager

HELLO_WORLD = "Hello World"
SEPARATOR = os.linesep if (os.name == "nt" and sys.version_info < (3,)) else "\n"
EXPECTED_LOGS = [
    'STEP_START - Started execution of step "easy".',
    'STEP_OUTPUT - Yielded output "result" of type "Any"',
    'STEP_SUCCESS - Finished execution of step "easy"',
]


@mock.patch("dagster_azure.blob.compute_log_manager.generate_blob_sas")
@mock.patch("dagster_azure.blob.compute_log_manager.create_blob_client")
def test_compute_log_manager(
    mock_create_blob_client, mock_generate_blob_sas, storage_account, container, credential
):
    mock_generate_blob_sas.return_value = "fake-url"
    fake_client = FakeBlobServiceClient(storage_account)
    mock_create_blob_client.return_value = fake_client

    @graph
    def simple():
        @op
        def easy(context):
            context.log.info("easy")
            print(HELLO_WORLD)  # noqa: T201
            return "easy"

        easy()

    with tempfile.TemporaryDirectory() as temp_dir:
        with environ({"DAGSTER_HOME": temp_dir}):
            run_store = SqliteRunStorage.from_local(temp_dir)
            event_store = SqliteEventLogStorage(temp_dir)
            manager = AzureBlobComputeLogManager(
                storage_account=storage_account,
                container=container,
                prefix="my_prefix",
                local_dir=temp_dir,
                secret_key=credential,
            )
            instance = DagsterInstance(
                instance_type=InstanceType.PERSISTENT,
                local_artifact_storage=LocalArtifactStorage(temp_dir),
                run_storage=run_store,
                event_storage=event_store,
                compute_log_manager=manager,
                run_coordinator=DefaultRunCoordinator(),
                run_launcher=SyncInMemoryRunLauncher(),
                ref=InstanceRef.from_dir(temp_dir),
                settings={"telemetry": {"enabled": False}},
            )
            result = simple.execute_in_process(instance=instance)
            capture_events = [
                event
                for event in result.all_events
                if event.event_type == DagsterEventType.LOGS_CAPTURED
            ]
            assert len(capture_events) == 1
            event = capture_events[0]
            file_key = event.logs_captured_data.file_key
            log_key = manager.build_log_key_for_run(result.run_id, file_key)

            # Capture API
            log_data = manager.get_log_data(log_key)
            stdout = log_data.stdout.decode("utf-8")
            assert stdout == HELLO_WORLD + SEPARATOR
            stderr = log_data.stderr.decode("utf-8")
            for expected in EXPECTED_LOGS:
                assert expected in stderr

            # Legacy API
            stdout = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDOUT)
            assert stdout.data == HELLO_WORLD + SEPARATOR

            stderr = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDERR)
            for expected in EXPECTED_LOGS:
                assert expected in stderr.data

            # Check ADLS2 directly
            adls2_object = fake_client.get_blob_client(
                container=container,
                blob=f"my_prefix/storage/{result.run_id}/compute_logs/{file_key}.err",
            )
            adls2_stderr = adls2_object.download_blob().readall().decode("utf-8")
            for expected in EXPECTED_LOGS:
                assert expected in adls2_stderr

            # Check download behavior by deleting locally cached logs
            compute_logs_dir = os.path.join(temp_dir, result.run_id, "compute_logs")
            for filename in os.listdir(compute_logs_dir):
                os.unlink(os.path.join(compute_logs_dir, filename))

            # Capture API
            log_data = manager.get_log_data(log_key)
            stdout = log_data.stdout.decode("utf-8")
            assert stdout == HELLO_WORLD + SEPARATOR
            stderr = log_data.stderr.decode("utf-8")
            for expected in EXPECTED_LOGS:
                assert expected in stderr

            # Legacy API
            stdout = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDOUT)
            assert stdout.data == HELLO_WORLD + SEPARATOR

            stderr = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDERR)
            for expected in EXPECTED_LOGS:
                assert expected in stderr.data


def test_compute_log_manager_from_config(storage_account, container, credential):
    prefix = "foobar"

    dagster_yaml = """
compute_logs:
  module: dagster_azure.blob.compute_log_manager
  class: AzureBlobComputeLogManager
  config:
    storage_account: "{storage_account}"
    container: {container}
    secret_key: {credential}
    local_dir: "/tmp/cool"
    prefix: "{prefix}"
""".format(
        storage_account=storage_account, container=container, credential=credential, prefix=prefix
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb") as f:
            f.write(dagster_yaml.encode("utf-8"))

        instance = DagsterInstance.from_config(tempdir)
    assert (
        instance.compute_log_manager._storage_account  # pylint: disable=protected-access
        == storage_account
    )
    assert instance.compute_log_manager._container == container  # pylint: disable=protected-access
    assert instance.compute_log_manager._blob_prefix == prefix  # pylint: disable=protected-access


@mock.patch("dagster_azure.blob.compute_log_manager.create_blob_client")
def test_prefix_filter(mock_create_blob_client, storage_account, container, credential):
    blob_prefix = "foo/bar/"  # note the trailing slash

    fake_client = FakeBlobServiceClient(storage_account)
    mock_create_blob_client.return_value = fake_client
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = AzureBlobComputeLogManager(
            storage_account=storage_account,
            container=container,
            prefix=blob_prefix,
            local_dir=temp_dir,
            secret_key=credential,
        )
        log_key = ["arbitrary", "log", "key"]
        with manager.open_log_stream(log_key, ComputeIOType.STDERR) as write_stream:
            write_stream.write("hello hello")

        adls2_object = fake_client.get_blob_client(
            container=container,
            blob="foo/bar/storage/arbitrary/log/key.err",
        )
        logs = adls2_object.download_blob().readall().decode("utf-8")
        assert logs == "hello hello"


class TestAzureComputeLogManager(TestCapturedLogManager):
    __test__ = True

    @pytest.fixture(name="captured_log_manager")
    def captured_log_manager(
        self,
        blob_client,
        storage_account,
        container,
        credential,
    ):  # pylint: disable=arguments-differ
        with mock.patch(
            "dagster_azure.blob.compute_log_manager.generate_blob_sas"
        ) as generate_blob_sas, mock.patch(
            "dagster_azure.blob.compute_log_manager.create_blob_client"
        ) as create_blob_client, tempfile.TemporaryDirectory() as temp_dir:
            generate_blob_sas.return_value = "fake-url"
            create_blob_client.return_value = blob_client

            yield AzureBlobComputeLogManager(
                storage_account=storage_account,
                container=container,
                prefix="my_prefix",
                local_dir=temp_dir,
                secret_key=credential,
            )

    # for streaming tests
    @pytest.fixture(name="write_manager")
    def write_manager(
        self,
        blob_client,
        storage_account,
        container,
        credential,
    ):  # pylint: disable=arguments-differ
        with mock.patch(
            "dagster_azure.blob.compute_log_manager.generate_blob_sas"
        ) as generate_blob_sas, mock.patch(
            "dagster_azure.blob.compute_log_manager.create_blob_client"
        ) as create_blob_client, tempfile.TemporaryDirectory() as temp_dir:
            generate_blob_sas.return_value = "fake-url"
            create_blob_client.return_value = blob_client

            yield AzureBlobComputeLogManager(
                storage_account=storage_account,
                container=container,
                prefix="my_prefix",
                local_dir=temp_dir,
                secret_key=credential,
                upload_interval=1,
            )

    @pytest.fixture(name="read_manager")
    def read_manager(self, captured_log_manager):  # pylint: disable=arguments-differ
        yield captured_log_manager


@mock.patch("dagster_azure.blob.compute_log_manager.DefaultAzureCredential")
@mock.patch("dagster_azure.blob.compute_log_manager.generate_blob_sas")
@mock.patch("dagster_azure.blob.compute_log_manager.create_blob_client")
def test_compute_log_manager_default_azure_credential(
    mock_create_blob_client,
    mock_generate_blob_sas,
    MockDefaultAzureCredential,
    storage_account,
    container,
):
    mock_generate_blob_sas.return_value = "fake-url"
    fake_client = FakeBlobServiceClient(storage_account)
    mock_create_blob_client.return_value = fake_client

    @graph
    def simple():
        @op
        def easy(context):
            context.log.info("easy")
            print(HELLO_WORLD)  # noqa: T201
            return "easy"

        easy()

    with tempfile.TemporaryDirectory() as temp_dir:
        with environ({"DAGSTER_HOME": temp_dir}):
            run_store = SqliteRunStorage.from_local(temp_dir)
            event_store = SqliteEventLogStorage(temp_dir)
            manager = AzureBlobComputeLogManager(
                storage_account=storage_account,
                container=container,
                prefix="my_prefix",
                local_dir=temp_dir,
                default_azure_credential={"exclude_environment_credentials": True},
            )
            instance = DagsterInstance(
                instance_type=InstanceType.PERSISTENT,
                local_artifact_storage=LocalArtifactStorage(temp_dir),
                run_storage=run_store,
                event_storage=event_store,
                compute_log_manager=manager,
                run_coordinator=DefaultRunCoordinator(),
                run_launcher=SyncInMemoryRunLauncher(),
                ref=InstanceRef.from_dir(temp_dir),
                settings={"telemetry": {"enabled": False}},
            )
            result = simple.execute_in_process(instance=instance)
            capture_events = [
                event
                for event in result.all_events
                if event.event_type == DagsterEventType.LOGS_CAPTURED
            ]
            assert len(capture_events) == 1
            MockDefaultAzureCredential.assert_called_once_with(exclude_environment_credentials=True)
            event = capture_events[0]
            file_key = event.logs_captured_data.file_key
            log_key = manager.build_log_key_for_run(result.run_id, file_key)

            # Capture API
            log_data = manager.get_log_data(log_key)
            stdout = log_data.stdout.decode("utf-8")
            assert stdout == HELLO_WORLD + SEPARATOR
            stderr = log_data.stderr.decode("utf-8")
            for expected in EXPECTED_LOGS:
                assert expected in stderr

            # Legacy API
            stdout = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDOUT)
            assert stdout.data == HELLO_WORLD + SEPARATOR

            stderr = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDERR)
            for expected in EXPECTED_LOGS:
                assert expected in stderr.data

            # Check ADLS2 directly
            adls2_object = fake_client.get_blob_client(
                container=container,
                blob=f"my_prefix/storage/{result.run_id}/compute_logs/{file_key}.err",
            )
            adls2_stderr = adls2_object.download_blob().readall().decode("utf-8")
            for expected in EXPECTED_LOGS:
                assert expected in adls2_stderr

            # Check download behavior by deleting locally cached logs
            compute_logs_dir = os.path.join(temp_dir, result.run_id, "compute_logs")
            for filename in os.listdir(compute_logs_dir):
                os.unlink(os.path.join(compute_logs_dir, filename))

            # Capture API
            log_data = manager.get_log_data(log_key)
            stdout = log_data.stdout.decode("utf-8")
            assert stdout == HELLO_WORLD + SEPARATOR
            stderr = log_data.stderr.decode("utf-8")
            for expected in EXPECTED_LOGS:
                assert expected in stderr

            # Legacy API
            stdout = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDOUT)
            assert stdout.data == HELLO_WORLD + SEPARATOR

            stderr = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDERR)
            for expected in EXPECTED_LOGS:
                assert expected in stderr.data


def test_compute_log_manager_from_config_default_azure_credential(storage_account, container):
    prefix = "foobar"

    dagster_yaml = """
compute_logs:
  module: dagster_azure.blob.compute_log_manager
  class: AzureBlobComputeLogManager
  config:
    storage_account: "{storage_account}"
    container: {container}
    local_dir: "/tmp/cool"
    prefix: "{prefix}"
    default_azure_credential:
      exclude_environment_credentials: true
""".format(
        storage_account=storage_account, container=container, prefix=prefix
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb") as f:
            f.write(dagster_yaml.encode("utf-8"))

        instance = DagsterInstance.from_config(tempdir)
    assert (
        instance.compute_log_manager._storage_account  # pylint: disable=protected-access
        == storage_account
    )
    assert instance.compute_log_manager._container == container  # pylint: disable=protected-access
    assert instance.compute_log_manager._blob_prefix == prefix  # pylint: disable=protected-access
    assert instance.compute_log_manager._default_azure_credential == {
        "exclude_environment_credentials": True
    }  # pylint: disable=protected-access
