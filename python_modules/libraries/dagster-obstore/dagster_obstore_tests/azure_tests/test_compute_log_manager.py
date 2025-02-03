import os
import sys
import tempfile

import obstore as obs
from dagster import DagsterEventType, graph, op
from dagster._core.instance import DagsterInstance, InstanceRef, InstanceType
from dagster._core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster._core.run_coordinator import DefaultRunCoordinator
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.event_log import SqliteEventLogStorage
from dagster._core.storage.local_compute_log_manager import IO_TYPE_EXTENSION
from dagster._core.storage.root import LocalArtifactStorage
from dagster._core.storage.runs import SqliteRunStorage
from dagster._core.test_utils import ensure_dagster_tests_import, environ
from dagster._time import get_current_datetime
from obstore.store import AzureStore

from dagster_obstore.azure import ADLSComputeLogManager

ensure_dagster_tests_import()

HELLO_WORLD = "Hello World"
SEPARATOR = os.linesep if (os.name == "nt" and sys.version_info < (3,)) else "\n"
EXPECTED_LOGS = [
    'STEP_START - Started execution of step "easy".',
    'STEP_OUTPUT - Yielded output "result" of type "Any"',
    'STEP_SUCCESS - Finished execution of step "easy"',
]


def test_compute_log_manager(
    azure_store: AzureStore, storage_account, container, start_azurite_server
):
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
            manager = ADLSComputeLogManager(
                storage_account=storage_account,
                container=container,
                prefix="my_prefix",
                allow_http=True,
                local_dir=temp_dir,
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
            stdout = log_data.stdout.decode("utf-8")  # pyright: ignore[reportOptionalMemberAccess]
            assert stdout == HELLO_WORLD + SEPARATOR
            stderr = log_data.stderr.decode("utf-8")  # pyright: ignore[reportOptionalMemberAccess]
            for expected in EXPECTED_LOGS:
                assert expected in stderr

            # Check ADLS2 directly
            adls2_stderr = (
                obs.get(
                    azure_store, f"my_prefix/storage/{result.run_id}/compute_logs/{file_key}.err"
                )
                .bytes()
                .to_bytes()
                .decode("utf-8")
            )

            for expected in EXPECTED_LOGS:
                assert expected in adls2_stderr

            # Check download behavior by deleting locally cached logs
            compute_logs_dir = os.path.join(temp_dir, result.run_id, "compute_logs")
            for filename in os.listdir(compute_logs_dir):
                os.unlink(os.path.join(compute_logs_dir, filename))

            # Capture API
            log_data = manager.get_log_data(log_key)
            stdout = log_data.stdout.decode("utf-8")  # pyright: ignore[reportOptionalMemberAccess]
            assert stdout == HELLO_WORLD + SEPARATOR
            stderr = log_data.stderr.decode("utf-8")  # pyright: ignore[reportOptionalMemberAccess]
            for expected in EXPECTED_LOGS:
                assert expected in stderr


def test_compute_log_manager_from_config(storage_account, container):
    prefix = "foobar"

    credential = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "tenant_id": "test_tenant",
    }

    dagster_yaml = f"""
compute_logs:
  module: dagster_obstore.azure.compute_log_manager
  class: ADLSComputeLogManager
  config:
    storage_account: "{storage_account}"
    container: {container}

    client_id: "{credential['client_id']}"
    client_secret: "{credential['client_secret']}"
    tenant_id: "{credential['tenant_id']}"
    local_dir: "/tmp/cool"
    prefix: "{prefix}"
"""

    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb") as f:
            f.write(dagster_yaml.encode("utf-8"))

        instance = DagsterInstance.from_config(tempdir)
    assert instance.compute_log_manager._storage_account == storage_account  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
    assert instance.compute_log_manager._container == container  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
    assert instance.compute_log_manager._prefix == prefix  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]


def test_prefix_filter(azure_store: AzureStore, storage_account, container, start_azurite_server):
    blob_prefix = "foo/bar/"  # note the trailing slash

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ADLSComputeLogManager(
            storage_account=storage_account,
            container=container,
            prefix=blob_prefix,
            local_dir=temp_dir,
            allow_http=True,
        )
        log_key = ["arbitrary", "log", "key"]
        with manager.open_log_stream(log_key, ComputeIOType.STDERR) as write_stream:
            write_stream.write("hello hello")  # pyright: ignore[reportOptionalMemberAccess]

        logs = (
            obs.get(azure_store, "foo/bar/storage/arbitrary/log/key.err")
            .bytes()
            .to_bytes()
            .decode("utf-8")
        )

        assert logs == "hello hello"


def test_get_log_keys_for_log_key_prefix(
    azure_store: AzureStore, storage_account, container, start_azurite_server
):
    evaluation_time = get_current_datetime()
    blob_prefix = "foo/bar/"  # note the trailing slash

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ADLSComputeLogManager(
            storage_account=storage_account,
            container=container,
            prefix=blob_prefix,
            local_dir=temp_dir,
            allow_http=True,
        )
        log_key_prefix = ["test_log_bucket", evaluation_time.strftime("%Y%m%d_%H%M%S")]

        def write_log_file(file_id: int, io_type: ComputeIOType):
            full_log_key = [*log_key_prefix, f"{file_id}"]
            with manager.open_log_stream(full_log_key, io_type) as f:
                f.write("foo")  # pyright: ignore[reportOptionalMemberAccess]

    log_keys = manager.get_log_keys_for_log_key_prefix(log_key_prefix, io_type=ComputeIOType.STDERR)
    assert len(log_keys) == 0

    for i in range(4):
        write_log_file(i, ComputeIOType.STDERR)

    log_keys = manager.get_log_keys_for_log_key_prefix(log_key_prefix, io_type=ComputeIOType.STDERR)
    assert sorted(log_keys) == [  # pyright: ignore[reportArgumentType]
        [*log_key_prefix, "0"],
        [*log_key_prefix, "1"],
        [*log_key_prefix, "2"],
        [*log_key_prefix, "3"],
    ]

    # write a different file type - azure blob compute log manager will create empty files for both file types
    # when using open_log_stream, sp manually create the file

    log_key = [*log_key_prefix, "4"]
    with manager.local_manager.open_log_stream(log_key, ComputeIOType.STDOUT) as f:
        f.write("foo")  # pyright: ignore[reportOptionalMemberAccess]
    blob_key = manager._blob_key(log_key, ComputeIOType.STDOUT)  # noqa: SLF001
    with open(
        manager.local_manager.get_captured_local_path(
            log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT]
        ),
        "rb",
    ) as data:
        obs.put(azure_store, blob_key, file=data)

    log_keys = manager.get_log_keys_for_log_key_prefix(log_key_prefix, io_type=ComputeIOType.STDERR)
    assert sorted(log_keys) == [  # pyright: ignore[reportArgumentType]
        [*log_key_prefix, "0"],
        [*log_key_prefix, "1"],
        [*log_key_prefix, "2"],
        [*log_key_prefix, "3"],
    ]


def test_compute_log_manager_from_config_default_azure_credential(storage_account, container):
    prefix = "foobar"

    dagster_yaml = f"""
compute_logs:
  module: dagster_obstore.azure.compute_log_manager
  class: ADLSComputeLogManager
  config:
    storage_account: "{storage_account}"
    container: {container}
    local_dir: "/tmp/cool"
    prefix: "{prefix}"
"""

    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb") as f:
            f.write(dagster_yaml.encode("utf-8"))

        instance = DagsterInstance.from_config(tempdir)
    assert instance.compute_log_manager._storage_account == storage_account  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
    assert instance.compute_log_manager._container == container  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
    assert instance.compute_log_manager._prefix == prefix  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
