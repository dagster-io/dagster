import os
import sys
import tempfile

import pytest
from botocore.exceptions import ClientError
from dagster_aws.s3 import S3ComputeLogManager

from dagster import DagsterEventType, job, op
from dagster.core.instance import DagsterInstance, InstanceRef, InstanceType
from dagster.core.launcher import DefaultRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.event_log import SqliteEventLogStorage
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import SqliteRunStorage
from dagster.core.test_utils import environ

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
            compute_steps = [
                event.step_key
                for event in result.all_node_events
                if event.event_type == DagsterEventType.STEP_START
            ]
            assert len(compute_steps) == 1
            step_key = compute_steps[0]

            stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
            assert stdout.data == HELLO_WORLD + SEPARATOR

            stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
            for expected in EXPECTED_LOGS:
                assert expected in stderr.data

            # Check S3 directly
            s3_object = mock_s3_bucket.Object(
                key=f"my_prefix/storage/{result.run_id}/compute_logs/easy.err"
            )
            stderr_s3 = s3_object.get()["Body"].read().decode("utf-8")
            for expected in EXPECTED_LOGS:
                assert expected in stderr_s3

            # Check download behavior by deleting locally cached logs
            compute_logs_dir = os.path.join(temp_dir, result.run_id, "compute_logs")
            for filename in os.listdir(compute_logs_dir):
                os.unlink(os.path.join(compute_logs_dir, filename))

            stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
            assert stdout.data == HELLO_WORLD + SEPARATOR

            stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
            for expected in EXPECTED_LOGS:
                assert expected in stderr.data


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
        with open(os.path.join(tempdir, "dagster.yaml"), "wb", encoding="utf8") as f:
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

            stderr_object = mock_s3_bucket.Object(
                key=f"{PREFIX}/storage/{result.run_id}/compute_logs/easy.err"
            ).get()
            assert stderr_object

            with pytest.raises(ClientError):
                # stdout is not uploaded because we do not print anything to stdout
                mock_s3_bucket.Object(
                    key=f"{PREFIX}/storage/{result.run_id}/compute_logs/easy.out"
                ).get()


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
