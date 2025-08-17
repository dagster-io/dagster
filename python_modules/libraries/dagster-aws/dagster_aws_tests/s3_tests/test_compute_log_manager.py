import os
import sys
import tempfile

import pytest
from botocore.exceptions import ClientError
from dagster import DagsterEventType, job, op
from dagster._core.instance import DagsterInstance, InstanceRef, InstanceType
from dagster._core.launcher import DefaultRunLauncher
from dagster._core.run_coordinator import DefaultRunCoordinator
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.event_log import SqliteEventLogStorage
from dagster._core.storage.local_compute_log_manager import IO_TYPE_EXTENSION
from dagster._core.storage.root import LocalArtifactStorage
from dagster._core.storage.runs import SqliteRunStorage
from dagster._core.test_utils import ensure_dagster_tests_import, environ, instance_for_test
from dagster._time import get_current_datetime

from dagster_aws.s3 import S3ComputeLogManager

ensure_dagster_tests_import()
from dagster_tests.storage_tests.test_compute_log_manager import TestComputeLogManager

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
        print(HELLO_WORLD)  # noqa: T201
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

            # verify locally cached logs are deleted after they are captured
            local_path = manager._local_manager.get_captured_local_path(  # noqa: SLF001
                log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT]
            )
            assert not os.path.exists(local_path)

            log_data = manager.get_log_data(log_key)
            stdout = log_data.stdout.decode("utf-8")  # pyright: ignore[reportOptionalMemberAccess]
            assert stdout == HELLO_WORLD + SEPARATOR

            stderr = log_data.stderr.decode("utf-8")  # pyright: ignore[reportOptionalMemberAccess]
            for expected in EXPECTED_LOGS:
                assert expected in stderr

            # Check S3 directly
            s3_object = mock_s3_bucket.Object(
                key=manager._s3_key(log_key, ComputeIOType.STDERR)  # noqa: SLF001
            )
            stderr_s3 = s3_object.get()["Body"].read().decode("utf-8")
            for expected in EXPECTED_LOGS:
                assert expected in stderr_s3

            log_data = manager.get_log_data(log_key)

            # Re-downloads the data to the local filesystem again
            assert os.path.exists(local_path)

            stdout = log_data.stdout.decode("utf-8")  # pyright: ignore[reportOptionalMemberAccess]
            assert stdout == HELLO_WORLD + SEPARATOR

            stderr = log_data.stderr.decode("utf-8")  # pyright: ignore[reportOptionalMemberAccess]
            for expected in EXPECTED_LOGS:
                assert expected in stderr


def test_compute_log_manager_from_config(mock_s3_bucket):
    s3_prefix = "foobar"

    dagster_yaml = f"""
compute_logs:
  module: dagster_aws.s3.compute_log_manager
  class: S3ComputeLogManager
  config:
    bucket: "{mock_s3_bucket.name}"
    local_dir: "/tmp/cool"
    prefix: "{s3_prefix}"
"""

    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb") as f:
            f.write(dagster_yaml.encode("utf-8"))

        instance = DagsterInstance.from_config(tempdir)
    assert instance.compute_log_manager._s3_bucket == mock_s3_bucket.name  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
    assert instance.compute_log_manager._s3_prefix == s3_prefix  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]


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
            stderr_object = mock_s3_bucket.Object(
                key=manager._s3_key(log_key, ComputeIOType.STDERR)  # noqa: SLF001
            )
            assert stderr_object

            with pytest.raises(ClientError):
                # stdout is not uploaded because we do not print anything to stdout
                mock_s3_bucket.Object(
                    key=manager._s3_key(log_key, ComputeIOType.STDOUT)  # noqa: SLF001
                ).get()


def test_blank_compute_logs(mock_s3_bucket):
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = S3ComputeLogManager(
            bucket=mock_s3_bucket.name, prefix="my_prefix", local_dir=temp_dir
        )

        # simulate subscription to an in-progress run, where there is no key in the bucket
        log_data = manager.get_log_data(["my_run_id", "compute_logs", "my_step_key"])

        assert not log_data.stdout
        assert not log_data.stderr


def test_prefix_filter(mock_s3_bucket):
    s3_prefix = "foo/bar/"  # note the trailing slash

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = S3ComputeLogManager(
            bucket=mock_s3_bucket.name, prefix=s3_prefix, local_dir=temp_dir
        )
        log_key = ["arbitrary", "log", "key"]
        with manager.open_log_stream(log_key, ComputeIOType.STDERR) as write_stream:
            write_stream.write("hello hello")  # pyright: ignore[reportOptionalMemberAccess]

        s3_object = mock_s3_bucket.Object(key="foo/bar/storage/arbitrary/log/key.err")
        logs = s3_object.get()["Body"].read().decode("utf-8")
        assert logs == "hello hello"


def test_get_log_keys_for_log_key_prefix(mock_s3_bucket):
    evaluation_time = get_current_datetime()
    s3_prefix = "foo/bar/"  # note the trailing slash

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = S3ComputeLogManager(
            bucket=mock_s3_bucket.name, prefix=s3_prefix, local_dir=temp_dir, skip_empty_files=True
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

    # write a different file type
    write_log_file(4, ComputeIOType.STDOUT)

    log_keys = manager.get_log_keys_for_log_key_prefix(log_key_prefix, io_type=ComputeIOType.STDERR)
    assert sorted(log_keys) == [  # pyright: ignore[reportArgumentType]
        [*log_key_prefix, "0"],
        [*log_key_prefix, "1"],
        [*log_key_prefix, "2"],
        [*log_key_prefix, "3"],
    ]


class TestS3ComputeLogManager(TestComputeLogManager):
    __test__ = True

    @pytest.fixture(name="compute_log_manager")
    def compute_log_manager(self, mock_s3_bucket):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield S3ComputeLogManager(
                bucket=mock_s3_bucket.name, prefix="my_prefix", local_dir=temp_dir
            )

    # for streaming tests
    @pytest.fixture(name="write_manager")
    def write_manager(self, mock_s3_bucket):
        # should be a different local directory as the read manager
        with tempfile.TemporaryDirectory() as temp_dir:
            yield S3ComputeLogManager(
                bucket=mock_s3_bucket.name,
                prefix="my_prefix",
                local_dir=temp_dir,
                upload_interval=1,
            )

    @pytest.fixture(name="read_manager")
    def read_manager(self, mock_s3_bucket):
        # should be a different local directory as the write manager
        with tempfile.TemporaryDirectory() as temp_dir:
            yield S3ComputeLogManager(
                bucket=mock_s3_bucket.name, prefix="my_prefix", local_dir=temp_dir
            )


def test_external_compute_log_manager(mock_s3_bucket):
    @op
    def my_op():
        print("hello out")  # noqa: T201
        print("hello error", file=sys.stderr)  # noqa: T201

    @job
    def my_job():
        my_op()

    with instance_for_test(
        overrides={
            "compute_logs": {
                "module": "dagster_aws.s3.compute_log_manager",
                "class": "S3ComputeLogManager",
                "config": {
                    "bucket": mock_s3_bucket.name,
                    "show_url_only": True,
                },
            },
        },
    ) as instance:
        result = my_job.execute_in_process(instance=instance)
        assert result.success
        assert result.run_id
        captured_log_entries = instance.all_logs(
            result.run_id, of_type=DagsterEventType.LOGS_CAPTURED
        )
        assert len(captured_log_entries) == 1
        entry = captured_log_entries[0]
        assert entry.dagster_event.logs_captured_data.external_stdout_url  # pyright: ignore[reportOptionalMemberAccess]
        assert entry.dagster_event.logs_captured_data.external_stderr_url  # pyright: ignore[reportOptionalMemberAccess]
