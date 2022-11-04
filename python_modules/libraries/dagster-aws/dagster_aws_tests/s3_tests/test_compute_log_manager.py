# pylint: disable=protected-access

import os
import sys
import tempfile
import time

import pytest
from botocore.exceptions import ClientError
from dagster_aws.s3 import S3ComputeLogManager

from dagster import DagsterEventType, job, op
from dagster._core.instance import DagsterInstance, InstanceRef, InstanceType
from dagster._core.launcher import DefaultRunLauncher
from dagster._core.run_coordinator import DefaultRunCoordinator
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.event_log import SqliteEventLogStorage
from dagster._core.storage.local_compute_log_manager import IO_TYPE_EXTENSION
from dagster._core.storage.root import LocalArtifactStorage
from dagster._core.storage.runs import SqliteRunStorage
from dagster._core.test_utils import environ
from dagster._utils import ensure_dir

HELLO_WORLD = "Hello World"
SEPARATOR = os.linesep if (os.name == "nt" and sys.version_info < (3,)) else "\n"
EXPECTED_LOGS = [
    'STEP_START - Started execution of step "easy".',
    'STEP_OUTPUT - Yielded output "result" of type "Any"',
    'STEP_SUCCESS - Finished execution of step "easy"',
]


def test_compute_log_manager(mock_s3_bucket):
    @op
    def easy(context):
        context.log.info("easy")
        print(HELLO_WORLD)  # pylint: disable=print-call
        return "easy"

    @job
    def simple():
        easy()

    with tempfile.TemporaryDirectory() as temp_dir:
        with environ({"DAGSTER_HOME": temp_dir}):
            run_store = SqliteRunStorage.from_local(temp_dir)
            event_store = SqliteEventLogStorage(temp_dir)
            manager = S3ComputeLogManager(
                bucket=mock_s3_bucket.name, prefix="my_prefix", local_dir=temp_dir
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
            log_data = manager.get_log_data(log_key)
            stdout = log_data.stdout.decode("utf-8")
            assert stdout == HELLO_WORLD + SEPARATOR

            stderr = log_data.stderr.decode("utf-8")
            for expected in EXPECTED_LOGS:
                assert expected in stderr

            # Check S3 directly
            s3_object = mock_s3_bucket.Object(key=manager._s3_key(log_key, ComputeIOType.STDERR))
            stderr_s3 = s3_object.get()["Body"].read().decode("utf-8")
            for expected in EXPECTED_LOGS:
                assert expected in stderr_s3

            # Check download behavior by deleting locally cached logs
            local_dir = os.path.dirname(
                manager._local_manager.get_captured_local_path(
                    log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT]
                )
            )
            for filename in os.listdir(local_dir):
                os.unlink(os.path.join(local_dir, filename))

            log_data = manager.get_log_data(log_key)
            stdout = log_data.stdout.decode("utf-8")
            assert stdout == HELLO_WORLD + SEPARATOR

            stderr = log_data.stderr.decode("utf-8")
            for expected in EXPECTED_LOGS:
                assert expected in stderr


def test_compute_log_manager_from_config(mock_s3_bucket):
    s3_prefix = "foobar"

    dagster_yaml = """
compute_logs:
  module: dagster_aws.s3.compute_log_manager
  class: S3ComputeLogManager
  config:
    bucket: "{s3_bucket}"
    local_dir: "/tmp/cool"
    prefix: "{s3_prefix}"
""".format(
        s3_bucket=mock_s3_bucket.name, s3_prefix=s3_prefix
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb") as f:
            f.write(dagster_yaml.encode("utf-8"))

        instance = DagsterInstance.from_config(tempdir)
    assert (
        instance.compute_log_manager._s3_bucket  # pylint: disable=protected-access
        == mock_s3_bucket.name
    )
    assert instance.compute_log_manager._s3_prefix == s3_prefix  # pylint: disable=protected-access


def test_compute_log_manager_skip_empty_upload(mock_s3_bucket):
    @op
    def easy(context):
        context.log.info("easy")

    @job
    def simple():
        easy()

    with tempfile.TemporaryDirectory() as temp_dir:
        with environ({"DAGSTER_HOME": temp_dir}):
            run_store = SqliteRunStorage.from_local(temp_dir)
            event_store = SqliteEventLogStorage(temp_dir)
            PREFIX = "my_prefix"
            manager = S3ComputeLogManager(
                bucket=mock_s3_bucket.name, prefix=PREFIX, skip_empty_files=True
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
            stderr_object = mock_s3_bucket.Object(
                key=manager._s3_key(log_key, ComputeIOType.STDERR)
            )
            assert stderr_object

            with pytest.raises(ClientError):
                # stdout is not uploaded because we do not print anything to stdout
                mock_s3_bucket.Object(key=manager._s3_key(log_key, ComputeIOType.STDOUT)).get()


def test_blank_compute_logs(mock_s3_bucket):
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = S3ComputeLogManager(
            bucket=mock_s3_bucket.name, prefix="my_prefix", local_dir=temp_dir
        )

        # simulate subscription to an in-progress run, where there is no key in the bucket
        stdout = manager.read_logs_file("my_run_id", "my_step_key", ComputeIOType.STDOUT)
        stderr = manager.read_logs_file("my_run_id", "my_step_key", ComputeIOType.STDERR)

        assert not stdout.data
        assert not stderr.data


def test_streaming(mock_s3_bucket):
    with tempfile.TemporaryDirectory() as temp_dir:
        write_manager = S3ComputeLogManager(
            bucket=mock_s3_bucket.name,
            local_dir=ensure_dir(os.path.join(temp_dir, "a")),
            upload_interval=1,
        )
        read_manager = S3ComputeLogManager(
            bucket=mock_s3_bucket.name, local_dir=ensure_dir(os.path.join(temp_dir, "b"))
        )
        log_key = ["arbitrary", "log", "key"]
        with write_manager.capture_logs(log_key) as _context:
            print("hello stdout")  # pylint: disable=print-call
            print("hello stderr", file=sys.stderr)  # pylint: disable=print-call

            # read before the write manager has a chance to upload partial results
            log_data = read_manager.get_log_data(log_key)
            assert not log_data.stdout
            assert not log_data.stderr

            # wait past the upload interval and then read again
            time.sleep(2)
            log_data = read_manager.get_log_data(log_key)
            assert log_data.stdout == b"hello stdout\n"
            assert log_data.stderr == b"hello stderr\n"

            # check the s3 bucket directly that only partial keys have been uploaded
            keys = {object.key for object in mock_s3_bucket.objects.all()}
            assert write_manager._s3_key(log_key, ComputeIOType.STDOUT) not in keys
            assert write_manager._s3_key(log_key, ComputeIOType.STDERR) not in keys
            assert write_manager._s3_key(log_key, ComputeIOType.STDOUT, partial=True) in keys
            assert write_manager._s3_key(log_key, ComputeIOType.STDERR, partial=True) in keys
