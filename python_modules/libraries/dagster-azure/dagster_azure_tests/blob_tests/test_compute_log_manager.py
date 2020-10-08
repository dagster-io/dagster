import os
import sys

import six
from dagster_azure.blob import AzureBlobComputeLogManager, FakeBlobServiceClient

from dagster import DagsterEventType, execute_pipeline, pipeline, seven, solid
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.event_log import SqliteEventLogStorage
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import SqliteRunStorage
from dagster.seven import mock

HELLO_WORLD = "Hello World"
SEPARATOR = os.linesep if (os.name == "nt" and sys.version_info < (3,)) else "\n"
EXPECTED_LOGS = [
    'STEP_START - Started execution of step "easy.compute".',
    'STEP_OUTPUT - Yielded output "result" of type "Any"',
    'STEP_SUCCESS - Finished execution of step "easy.compute"',
]


@mock.patch("dagster_azure.blob.compute_log_manager.generate_blob_sas")
@mock.patch("dagster_azure.blob.compute_log_manager.create_blob_client")
def test_compute_log_manager(
    mock_create_blob_client, mock_generate_blob_sas, storage_account, container, credential
):
    mock_generate_blob_sas.return_value = "fake-url"
    fake_client = FakeBlobServiceClient(storage_account)
    mock_create_blob_client.return_value = fake_client

    @pipeline
    def simple():
        @solid
        def easy(context):
            context.log.info("easy")
            print(HELLO_WORLD)
            return "easy"

        easy()

    with seven.TemporaryDirectory() as temp_dir:
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
            run_launcher=SyncInMemoryRunLauncher(),
        )
        result = execute_pipeline(simple, instance=instance)
        compute_steps = [
            event.step_key
            for event in result.step_event_list
            if event.event_type == DagsterEventType.STEP_START
        ]
        assert len(compute_steps) == 1
        step_key = compute_steps[0]

        stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
        assert stdout.data == HELLO_WORLD + SEPARATOR

        stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
        for expected in EXPECTED_LOGS:
            assert expected in stderr.data

        # Check ADLS2 directly
        adls2_object = fake_client.get_blob_client(
            container=container,
            blob="{prefix}/storage/{run_id}/compute_logs/easy.compute.err".format(
                prefix="my_prefix", run_id=result.run_id
            ),
        )
        adls2_stderr = six.ensure_str(adls2_object.download_blob().readall())
        for expected in EXPECTED_LOGS:
            assert expected in adls2_stderr

        # Check download behavior by deleting locally cached logs
        compute_logs_dir = os.path.join(temp_dir, result.run_id, "compute_logs")
        for filename in os.listdir(compute_logs_dir):
            os.unlink(os.path.join(compute_logs_dir, filename))

        stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
        assert stdout.data == HELLO_WORLD + SEPARATOR

        stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
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

    with seven.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb") as f:
            f.write(six.ensure_binary(dagster_yaml))

        instance = DagsterInstance.from_config(tempdir)
    assert (
        instance.compute_log_manager._storage_account  # pylint: disable=protected-access
        == storage_account
    )
    assert instance.compute_log_manager._container == container  # pylint: disable=protected-access
    assert instance.compute_log_manager._blob_prefix == prefix  # pylint: disable=protected-access
