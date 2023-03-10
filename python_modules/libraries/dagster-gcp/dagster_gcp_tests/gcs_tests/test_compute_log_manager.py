import os
import sys
import tempfile
from unittest import mock

import pendulum
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
from dagster._core.test_utils import environ
from dagster_gcp.gcs import GCSComputeLogManager
from dagster_tests.storage_tests.test_captured_log_manager import TestCapturedLogManager
from google.cloud import storage

HELLO_WORLD = "Hello World"
SEPARATOR = os.linesep if (os.name == "nt" and sys.version_info < (3,)) else "\n"
EXPECTED_LOGS = [
    'STEP_START - Started execution of step "easy".',
    'STEP_OUTPUT - Yielded output "result" of type "Any"',
    'STEP_SUCCESS - Finished execution of step "easy"',
]


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


def test_compute_log_manager_with_envvar(gcs_bucket):
    @job
    def simple():
        @op
        def easy(context):
            context.log.info("easy")
            print(HELLO_WORLD)  # noqa: T201
            return "easy"

        easy()

    with open(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"), encoding="utf8") as f:
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
                stdout = log_data.stdout.decode("utf-8")
                assert stdout == HELLO_WORLD + SEPARATOR

                # legacy API
                stdout = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDOUT)
                assert stdout.data == HELLO_WORLD + SEPARATOR

                stderr = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDERR)
                for expected in EXPECTED_LOGS:
                    assert expected in stderr.data

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
                stdout = log_data.stdout.decode("utf-8")
                assert stdout == HELLO_WORLD + SEPARATOR

                # legacy API
                stdout = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDOUT)
                assert stdout.data == HELLO_WORLD + SEPARATOR

                stderr = manager.read_logs_file(result.run_id, file_key, ComputeIOType.STDERR)
                for expected in EXPECTED_LOGS:
                    assert expected in stderr.data


def test_compute_log_manager_from_config(gcs_bucket):
    gcs_prefix = "foobar"

    dagster_yaml = """
compute_logs:
  module: dagster_gcp.gcs.compute_log_manager
  class: GCSComputeLogManager
  config:
    bucket: "{bucket}"
    local_dir: "/tmp/cool"
    prefix: "{prefix}"
""".format(
        bucket=gcs_bucket, prefix=gcs_prefix
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb") as f:
            f.write(dagster_yaml.encode("utf-8"))

        instance = DagsterInstance.from_config(tempdir)

    assert isinstance(instance.compute_log_manager, GCSComputeLogManager)


def test_prefix_filter(gcs_bucket):
    gcs_prefix = "foo/bar/"  # note the trailing slash

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = GCSComputeLogManager(bucket=gcs_bucket, prefix=gcs_prefix, local_dir=temp_dir)
        time_str = pendulum.now("UTC").strftime("%Y_%m_%d__%H_%M_%S")
        log_key = ["arbitrary", "log", "key", time_str]
        with manager.open_log_stream(log_key, ComputeIOType.STDERR) as write_stream:
            write_stream.write("hello hello")

        logs = (
            storage.Client()
            .bucket(gcs_bucket)
            .blob(f"foo/bar/storage/arbitrary/log/key/{time_str}.err")
            .download_as_bytes()
            .decode("utf-8")
        )
        assert logs == "hello hello"


def test_storage_download_url_fallback(gcs_bucket):
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = GCSComputeLogManager(bucket=gcs_bucket, local_dir=temp_dir)
        time_str = pendulum.now("UTC").strftime("%Y_%m_%d__%H_%M_%S")
        log_key = ["arbitrary", "log", "key", time_str]

        orig_blob_fn = manager._bucket.blob
        with mock.patch.object(manager._bucket, "blob") as blob_fn:

            def _return_mocked_blob(*args, **kwargs):
                blob = orig_blob_fn(*args, **kwargs)
                blob.generate_signed_url = mock.Mock().side_effect = Exception("unauthorized")
                return blob

            blob_fn.side_effect = _return_mocked_blob

            with manager.open_log_stream(log_key, ComputeIOType.STDERR) as write_stream:
                write_stream.write("hello hello")

            # can read bytes
            log_data, _ = manager.log_data_for_type(log_key, ComputeIOType.STDERR, 0, None)
            assert log_data.decode("utf-8") == "hello hello"

            url = manager.download_url_for_type(log_key, ComputeIOType.STDERR)
            assert url.startswith("/logs")  # falls back to local storage url


class TestGCSComputeLogManager(TestCapturedLogManager):
    __test__ = True

    @pytest.fixture(name="captured_log_manager")
    def captured_log_manager(self, gcs_bucket):  # pylint: disable=arguments-differ
        with tempfile.TemporaryDirectory() as temp_dir:
            yield GCSComputeLogManager(bucket=gcs_bucket, prefix="my_prefix", local_dir=temp_dir)

    # for streaming tests
    @pytest.fixture(name="write_manager")
    def write_manager(self, gcs_bucket):  # pylint: disable=arguments-differ
        # should be a different local directory as the read manager
        with tempfile.TemporaryDirectory() as temp_dir:
            yield GCSComputeLogManager(
                bucket=gcs_bucket,
                prefix="my_prefix",
                local_dir=temp_dir,
                upload_interval=1,
            )

    @pytest.fixture(name="read_manager")
    def read_manager(self, gcs_bucket):  # pylint: disable=arguments-differ
        # should be a different local directory as the write manager
        with tempfile.TemporaryDirectory() as temp_dir:
            yield GCSComputeLogManager(bucket=gcs_bucket, prefix="my_prefix", local_dir=temp_dir)
