import os
import sys
import tempfile
from typing import cast
from unittest import mock

import pytest
from dagster import DagsterEventType, job, op
from dagster._core.instance import DagsterInstance, InstanceType
from dagster._core.instance.ref import InstanceRef
from dagster._core.launcher import DefaultRunLauncher
from dagster._core.run_coordinator import DefaultRunCoordinator
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.event_log import SqliteEventLogStorage
from dagster._core.storage.root import LocalArtifactStorage
from dagster._core.storage.runs import SqliteRunStorage
from dagster._core.test_utils import ensure_dagster_tests_import, environ, instance_for_test
from dagster._time import get_current_datetime
from dagster_gcp.gcs import GCSComputeLogManager
from google.cloud import storage

ensure_dagster_tests_import()
from dagster_tests.storage_tests.test_compute_log_manager import TestComputeLogManager

HELLO_WORLD = "Hello World"
SEPARATOR = os.linesep if (os.name == "nt" and sys.version_info < (3,)) else "\n"
EXPECTED_LOGS = [
    'STEP_START - Started execution of step "easy".',
    'STEP_OUTPUT - Yielded output "result" of type "Any"',
    'STEP_SUCCESS - Finished execution of step "easy"',
]


@pytest.mark.integration
def test_compute_log_manager(gcs_bucket):
    @job
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
            manager = GCSComputeLogManager(
                bucket=gcs_bucket, prefix="my_prefix", local_dir=temp_dir
            )
            instance = DagsterInstance(
                instance_type=InstanceType.PERSISTENT,
                local_artifact_storage=LocalArtifactStorage(temp_dir),
                run_storage=run_store,
                event_storage=event_store,
                compute_log_manager=manager,
                run_coordinator=DefaultRunCoordinator(),
                run_launcher=DefaultRunLauncher(),
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

            # Check GCS directly
            stderr_gcs = (
                storage.Client()
                .bucket(gcs_bucket)
                .blob(f"my_prefix/storage/{result.run_id}/compute_logs/{file_key}.err")
                .download_as_bytes()
                .decode("utf-8")
            )

            for expected in EXPECTED_LOGS:
                assert expected in stderr_gcs

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


@pytest.mark.integration
def test_compute_log_manager_with_envvar(gcs_bucket):
    @job
    def simple():
        @op
        def easy(context):
            context.log.info("easy")
            print(HELLO_WORLD)  # noqa: T201
            return "easy"

        easy()

    with open(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"), encoding="utf8") as f:  # pyright: ignore[reportArgumentType]
        with tempfile.TemporaryDirectory() as temp_dir:
            with environ({"ENV_VAR": f.read(), "DAGSTER_HOME": temp_dir}):
                run_store = SqliteRunStorage.from_local(temp_dir)
                event_store = SqliteEventLogStorage(temp_dir)
                manager = GCSComputeLogManager(
                    bucket=gcs_bucket,
                    prefix="my_prefix",
                    local_dir=temp_dir,
                    json_credentials_envvar="ENV_VAR",
                )
                instance = DagsterInstance(
                    instance_type=InstanceType.PERSISTENT,
                    local_artifact_storage=LocalArtifactStorage(temp_dir),
                    run_storage=run_store,
                    event_storage=event_store,
                    compute_log_manager=manager,
                    run_coordinator=DefaultRunCoordinator(),
                    run_launcher=DefaultRunLauncher(),
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

                # capture API
                log_data = manager.get_log_data(log_key)
                stdout = log_data.stdout.decode("utf-8")  # pyright: ignore[reportOptionalMemberAccess]
                assert stdout == HELLO_WORLD + SEPARATOR

                # Check GCS directly
                stderr_gcs = (
                    storage.Client()
                    .bucket(gcs_bucket)
                    .blob(f"my_prefix/storage/{result.run_id}/compute_logs/{file_key}.err")
                    .download_as_bytes()
                    .decode("utf-8")
                )

                for expected in EXPECTED_LOGS:
                    assert expected in stderr_gcs

                # Check download behavior by deleting locally cached logs
                compute_logs_dir = os.path.join(temp_dir, result.run_id, "compute_logs")
                for filename in os.listdir(compute_logs_dir):
                    os.unlink(os.path.join(compute_logs_dir, filename))

                # capture API
                log_data = manager.get_log_data(log_key)
                stdout = log_data.stdout.decode("utf-8")  # pyright: ignore[reportOptionalMemberAccess]
                assert stdout == HELLO_WORLD + SEPARATOR


@pytest.mark.integration
def test_compute_log_manager_from_config(gcs_bucket):
    gcs_prefix = "foobar"

    dagster_yaml = f"""
compute_logs:
  module: dagster_gcp.gcs.compute_log_manager
  class: GCSComputeLogManager
  config:
    bucket: "{gcs_bucket}"
    local_dir: "/tmp/cool"
    prefix: "{gcs_prefix}"
"""

    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb") as f:
            f.write(dagster_yaml.encode("utf-8"))

        instance = DagsterInstance.from_config(tempdir)

    assert isinstance(instance.compute_log_manager, GCSComputeLogManager)


@pytest.mark.integration
def test_external_compute_log_manager(gcs_bucket):
    gcs_prefix = "foobar"

    @job
    def simple():
        @op
        def easy(context):
            context.log.info("easy")
            print(HELLO_WORLD)  # noqa: T201
            return "easy"

        easy()

    with instance_for_test(
        {
            "compute_logs": {
                "module": "dagster_gcp.gcs.compute_log_manager",
                "class": "GCSComputeLogManager",
                "config": {
                    "bucket": gcs_bucket,
                    "local_dir": "/tmp/cool",
                    "prefix": gcs_prefix,
                    "show_url_only": True,
                },
            }
        }
    ) as instance:
        assert isinstance(instance.compute_log_manager, GCSComputeLogManager)
        assert cast(GCSComputeLogManager, instance.compute_log_manager)._show_url_only  # noqa
        result = simple.execute_in_process(instance=instance)
        captured_log_entries = instance.all_logs(
            result.run_id, of_type=DagsterEventType.LOGS_CAPTURED
        )
        assert len(captured_log_entries) == 1
        entry = captured_log_entries[0]
        assert entry.dagster_event.logs_captured_data.external_stdout_url  # pyright: ignore[reportOptionalMemberAccess]
        assert entry.dagster_event.logs_captured_data.external_stderr_url  # pyright: ignore[reportOptionalMemberAccess]


@pytest.mark.integration
def test_prefix_filter(gcs_bucket):
    gcs_prefix = "foo/bar/"  # note the trailing slash

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = GCSComputeLogManager(bucket=gcs_bucket, prefix=gcs_prefix, local_dir=temp_dir)
        time_str = get_current_datetime().strftime("%Y_%m_%d__%H_%M_%S")
        log_key = ["arbitrary", "log", "key", time_str]
        with manager.open_log_stream(log_key, ComputeIOType.STDERR) as write_stream:
            write_stream.write("hello hello")  # pyright: ignore[reportOptionalMemberAccess]

        logs = (
            storage.Client()
            .bucket(gcs_bucket)
            .blob(f"foo/bar/storage/arbitrary/log/key/{time_str}.err")
            .download_as_bytes()
            .decode("utf-8")
        )
        assert logs == "hello hello"


@pytest.mark.integration
def test_get_log_keys_for_log_key_prefix(gcs_bucket):
    evaluation_time = get_current_datetime()
    gcs_prefix = "foo/bar/"  # note the trailing slash

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = GCSComputeLogManager(bucket=gcs_bucket, prefix=gcs_prefix, local_dir=temp_dir)
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

    # gcs creates and stores empty files for both IOTYPES when open_log_stream is used, so make the next file
    # manually so we can test that files with different IOTYPES are not considered

    log_key = [*log_key_prefix, "4"]
    with manager.local_manager.open_log_stream(log_key, ComputeIOType.STDOUT) as f:
        f.write("foo")  # pyright: ignore[reportOptionalMemberAccess]
    manager.upload_to_cloud_storage(log_key, ComputeIOType.STDOUT)

    log_keys = manager.get_log_keys_for_log_key_prefix(log_key_prefix, io_type=ComputeIOType.STDERR)
    assert sorted(log_keys) == [  # pyright: ignore[reportArgumentType]
        [*log_key_prefix, "0"],
        [*log_key_prefix, "1"],
        [*log_key_prefix, "2"],
        [*log_key_prefix, "3"],
    ]


@pytest.mark.integration
def test_storage_download_url_fallback(gcs_bucket):
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = GCSComputeLogManager(bucket=gcs_bucket, local_dir=temp_dir)
        time_str = get_current_datetime().strftime("%Y_%m_%d__%H_%M_%S")
        log_key = ["arbitrary", "log", "key", time_str]

        orig_blob_fn = manager._bucket.blob  # noqa: SLF001
        with mock.patch.object(manager._bucket, "blob") as blob_fn:  # noqa: SLF001

            def _return_mocked_blob(*args, **kwargs):
                blob = orig_blob_fn(*args, **kwargs)
                blob.generate_signed_url = mock.Mock().side_effect = Exception("unauthorized")
                return blob

            blob_fn.side_effect = _return_mocked_blob

            with manager.open_log_stream(log_key, ComputeIOType.STDERR) as write_stream:
                write_stream.write("hello hello")  # pyright: ignore[reportOptionalMemberAccess]

            # can read bytes
            log_data, _ = manager.get_log_data_for_type(log_key, ComputeIOType.STDERR, 0, None)
            assert log_data
            assert log_data.decode("utf-8") == "hello hello"

            url = manager.download_url_for_type(log_key, ComputeIOType.STDERR)
            assert url
            assert url.startswith("/logs")  # falls back to local storage url


@pytest.mark.integration
class TestGCSComputeLogManager(TestComputeLogManager):
    __test__ = True

    @pytest.fixture(name="compute_log_manager")
    def compute_log_manager(self, gcs_bucket):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield GCSComputeLogManager(bucket=gcs_bucket, prefix="my_prefix", local_dir=temp_dir)

    # for streaming tests
    @pytest.fixture(name="write_manager")
    def write_manager(self, gcs_bucket):
        # should be a different local directory as the read manager
        with tempfile.TemporaryDirectory() as temp_dir:
            yield GCSComputeLogManager(
                bucket=gcs_bucket,
                prefix="my_prefix",
                local_dir=temp_dir,
                upload_interval=1,
            )

    @pytest.fixture(name="read_manager")
    def read_manager(self, gcs_bucket):
        # should be a different local directory as the write manager
        with tempfile.TemporaryDirectory() as temp_dir:
            yield GCSComputeLogManager(bucket=gcs_bucket, prefix="my_prefix", local_dir=temp_dir)
