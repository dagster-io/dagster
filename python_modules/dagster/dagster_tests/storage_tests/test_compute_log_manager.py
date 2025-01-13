import tempfile
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from typing import IO, Optional

import dagster._check as check
from dagster import job, op
from dagster._core.instance import DagsterInstance, InstanceRef, InstanceType
from dagster._core.launcher import DefaultRunLauncher
from dagster._core.run_coordinator import DefaultRunCoordinator
from dagster._core.storage.compute_log_manager import (
    CapturedLogContext,
    CapturedLogMetadata,
    CapturedLogSubscription,
    ComputeIOType,
    ComputeLogManager,
)
from dagster._core.storage.event_log import SqliteEventLogStorage
from dagster._core.storage.root import LocalArtifactStorage
from dagster._core.storage.runs import SqliteRunStorage
from dagster._core.test_utils import environ, instance_for_test

from dagster_tests.storage_tests.utils.compute_log_manager import TestComputeLogManager


class BrokenComputeLogManager(ComputeLogManager):
    def __init__(self, fail_on_setup=False, fail_on_teardown=False):
        self._fail_on_setup = check.opt_bool_param(fail_on_setup, "fail_on_setup")
        self._fail_on_teardown = check.opt_bool_param(fail_on_teardown, "fail_on_teardown")

    @contextmanager
    def capture_logs(self, log_key: Sequence[str]) -> Generator[CapturedLogContext, None, None]:
        if self._fail_on_setup:
            raise Exception("fail on setup")
        yield CapturedLogContext(log_key=log_key)
        if self._fail_on_teardown:
            raise Exception("fail on teardown")

    @contextmanager
    def open_log_stream(
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Generator[Optional[IO], None, None]:
        yield None

    def is_capture_complete(self, log_key: Sequence[str]) -> bool:
        return True

    def get_log_data_for_type(
        self,
        log_key: Sequence[str],
        io_type: ComputeIOType,
        offset: int,
        max_bytes: Optional[int],
    ) -> tuple[Optional[bytes], int]:
        return None, 0

    def get_log_metadata(self, log_key: Sequence[str]) -> CapturedLogMetadata:
        return CapturedLogMetadata()

    def delete_logs(
        self, log_key: Optional[Sequence[str]] = None, prefix: Optional[Sequence[str]] = None
    ):
        pass

    def subscribe(
        self, log_key: Sequence[str], cursor: Optional[str] = None
    ) -> CapturedLogSubscription:
        return CapturedLogSubscription(self, log_key, cursor)

    def unsubscribe(self, subscription: CapturedLogSubscription):
        return


@contextmanager
def broken_compute_log_manager_instance(fail_on_setup=False, fail_on_teardown=False):
    with tempfile.TemporaryDirectory() as temp_dir:
        with environ({"DAGSTER_HOME": temp_dir}):
            yield DagsterInstance(
                instance_type=InstanceType.PERSISTENT,
                local_artifact_storage=LocalArtifactStorage(temp_dir),
                run_storage=SqliteRunStorage.from_local(temp_dir),
                event_storage=SqliteEventLogStorage(temp_dir),
                compute_log_manager=BrokenComputeLogManager(
                    fail_on_setup=fail_on_setup, fail_on_teardown=fail_on_teardown
                ),
                run_coordinator=DefaultRunCoordinator(),
                run_launcher=DefaultRunLauncher(),
                ref=InstanceRef.from_dir(temp_dir),
            )


def _has_setup_exception(execute_result):
    return any(
        [
            "Exception while setting up compute log capture" in str(event)
            for event in execute_result.all_events
        ]
    )


def _has_teardown_exception(execute_result):
    return any(
        [
            "Exception while cleaning up compute log capture" in str(event)
            for event in execute_result.all_events
        ]
    )


@op
def yay(context):
    context.log.info("yay")
    print("HELLOOO")  # noqa: T201
    return "yay"


@op
def boo(context):
    context.log.info("boo")
    print("HELLOOO")  # noqa: T201
    raise Exception("booo")


@job
def yay_job():
    yay()


@job
def boo_job():
    boo()


def test_broken_compute_log_manager():
    with broken_compute_log_manager_instance(fail_on_setup=True) as instance:
        yay_result = yay_job.execute_in_process(instance=instance)
        assert yay_result.success
        assert _has_setup_exception(yay_result)

        boo_result = boo_job.execute_in_process(instance=instance, raise_on_error=False)
        assert not boo_result.success
        assert _has_setup_exception(boo_result)

    with broken_compute_log_manager_instance(fail_on_teardown=True) as instance:
        yay_result = yay_job.execute_in_process(instance=instance)
        assert yay_result.success
        assert _has_teardown_exception(yay_result)

        boo_result = boo_job.execute_in_process(instance=instance, raise_on_error=False)

        assert not boo_result.success
        assert _has_teardown_exception(boo_result)

    with broken_compute_log_manager_instance() as instance:
        yay_result = yay_job.execute_in_process(instance=instance)
        assert yay_result.success
        assert not _has_setup_exception(yay_result)
        assert not _has_teardown_exception(yay_result)

        boo_result = boo_job.execute_in_process(instance=instance, raise_on_error=False)
        assert not boo_result.success
        assert not _has_setup_exception(boo_result)
        assert not _has_teardown_exception(boo_result)


import os
import sys
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any

import pytest
from dagster import job, op
from dagster._core.events import DagsterEventType
from dagster._core.storage.compute_log_manager import CapturedLogContext, ComputeIOType
from dagster._core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster._serdes import ConfigurableClassData
from dagster._time import get_current_datetime
from typing_extensions import Self


def test_compute_log_manager_instance():
    with instance_for_test() as instance:
        assert instance.compute_log_manager
        assert instance.compute_log_manager._instance  # noqa: SLF001


class TestLocalComputeLogManager(TestComputeLogManager):
    __test__ = True

    @pytest.fixture(name="compute_log_manager")
    def compute_log_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir_path:
            return LocalComputeLogManager(tmpdir_path)


class ExternalTestComputeLogManager(NoOpComputeLogManager):
    """Test compute log manager that does not actually capture logs, but generates an external url
    to be shown within the Dagster UI.
    """

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)

    def enabled(self, _dagster_run, _step_key):
        return True

    @contextmanager
    def capture_logs(self, log_key: Sequence[str]) -> Generator[CapturedLogContext, None, None]:
        yield CapturedLogContext(
            log_key=log_key,
            external_stdout_url="https://fake.com/stdout",
            external_stderr_url="https://fake.com/stderr",
        )


def test_external_compute_log_manager():
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
                "module": "dagster_tests.storage_tests.test_compute_log_manager",
                "class": "ExternalTestComputeLogManager",
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
        assert (
            entry.dagster_event.logs_captured_data.external_stdout_url == "https://fake.com/stdout"  # pyright: ignore[reportOptionalMemberAccess]
        )
        assert (
            entry.dagster_event.logs_captured_data.external_stderr_url == "https://fake.com/stderr"  # pyright: ignore[reportOptionalMemberAccess]
        )


def test_get_log_keys_for_log_key_prefix():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        cm = LocalComputeLogManager(tmpdir_path)
        evaluation_time = get_current_datetime()
        log_key_prefix = ["test_log_bucket", evaluation_time.strftime("%Y%m%d_%H%M%S")]

        def write_log_file(file_id: int):
            full_log_key = [*log_key_prefix, f"{file_id}"]
            with cm.open_log_stream(full_log_key, ComputeIOType.STDERR) as f:
                f.write("foo")  # pyright: ignore[reportOptionalMemberAccess]

        for i in range(4):
            write_log_file(i)

        log_keys = cm.get_log_keys_for_log_key_prefix(log_key_prefix, io_type=ComputeIOType.STDERR)
        assert sorted(log_keys) == [  # pyright: ignore[reportArgumentType]
            [*log_key_prefix, "0"],
            [*log_key_prefix, "1"],
            [*log_key_prefix, "2"],
            [*log_key_prefix, "3"],
        ]


def test_read_log_lines_for_log_key_prefix():
    """Tests that we can read a sequence of files in a bucket as if they are a single file."""
    with tempfile.TemporaryDirectory() as tmpdir_path:
        cm = LocalComputeLogManager(tmpdir_path)
        evaluation_time = get_current_datetime()
        log_key_prefix = ["test_log_bucket", evaluation_time.strftime("%Y%m%d_%H%M%S")]

        all_logs = []

        def write_log_file(file_id: int):
            full_log_key = [*log_key_prefix, f"{file_id}"]
            with cm.open_log_stream(full_log_key, ComputeIOType.STDERR) as f:
                num_lines = 10
                for j in range(num_lines):
                    msg = f"file: {file_id}, line: {j}"
                    all_logs.append(msg)
                    f.write(msg)  # pyright: ignore[reportOptionalMemberAccess]
                    if j < num_lines - 1:
                        f.write("\n")  # pyright: ignore[reportOptionalMemberAccess]

        for i in range(4):
            write_log_file(i)

        all_logs_iter = iter(all_logs)

        os.environ["DAGSTER_CAPTURED_LOG_CHUNK_SIZE"] = "10"
        # read the entirety of the first file
        log_lines, cursor = cm.read_log_lines_for_log_key_prefix(
            log_key_prefix, cursor=None, io_type=ComputeIOType.STDERR
        )
        assert len(log_lines) == 10
        assert cursor.has_more_now  # pyright: ignore[reportOptionalMemberAccess]
        assert cursor.log_key == [*log_key_prefix, "1"]  # pyright: ignore[reportOptionalMemberAccess]
        assert cursor.line == 0  # pyright: ignore[reportOptionalMemberAccess]
        for ll in log_lines:
            assert ll == next(all_logs_iter)

        # read half of the next log file
        os.environ["DAGSTER_CAPTURED_LOG_CHUNK_SIZE"] = "5"
        log_lines, cursor = cm.read_log_lines_for_log_key_prefix(
            log_key_prefix,
            cursor=cursor.to_string(),  # pyright: ignore[reportOptionalMemberAccess]
            io_type=ComputeIOType.STDERR,
        )
        assert len(log_lines) == 5
        assert cursor.has_more_now  # pyright: ignore[reportOptionalMemberAccess]
        assert cursor.log_key == [*log_key_prefix, "1"]  # pyright: ignore[reportOptionalMemberAccess]
        assert cursor.line == 5  # pyright: ignore[reportOptionalMemberAccess]
        for ll in log_lines:
            assert ll == next(all_logs_iter)

        # read the next ten lines, five will be in the second file, five will be in the third
        os.environ["DAGSTER_CAPTURED_LOG_CHUNK_SIZE"] = "10"
        log_lines, cursor = cm.read_log_lines_for_log_key_prefix(
            log_key_prefix,
            cursor=cursor.to_string(),  # pyright: ignore[reportOptionalMemberAccess]
            io_type=ComputeIOType.STDERR,
        )
        assert len(log_lines) == 10
        assert cursor.has_more_now  # pyright: ignore[reportOptionalMemberAccess]
        assert cursor.log_key == [*log_key_prefix, "2"]  # pyright: ignore[reportOptionalMemberAccess]
        assert cursor.line == 5  # pyright: ignore[reportOptionalMemberAccess]
        for ll in log_lines:
            assert ll == next(all_logs_iter)

        # read the remaining 15 lines, but request 20
        os.environ["DAGSTER_CAPTURED_LOG_CHUNK_SIZE"] = "20"
        log_lines, cursor = cm.read_log_lines_for_log_key_prefix(
            log_key_prefix,
            cursor=cursor.to_string(),  # pyright: ignore[reportOptionalMemberAccess]
            io_type=ComputeIOType.STDERR,
        )
        assert len(log_lines) == 15
        assert not cursor.has_more_now  # pyright: ignore[reportOptionalMemberAccess]
        assert cursor.log_key == [*log_key_prefix, "3"]  # pyright: ignore[reportOptionalMemberAccess]
        # processed up to the end of the file, but there is not another file to process so cursor should be -1
        assert cursor.line == -1  # pyright: ignore[reportOptionalMemberAccess]
        for ll in log_lines:
            assert ll == next(all_logs_iter)

        # write a final log file

        write_log_file(4)

        os.environ["DAGSTER_CAPTURED_LOG_CHUNK_SIZE"] = "15"
        log_lines, cursor = cm.read_log_lines_for_log_key_prefix(
            log_key_prefix,
            cursor=cursor.to_string(),  # pyright: ignore[reportOptionalMemberAccess]
            io_type=ComputeIOType.STDERR,
        )
        assert len(log_lines) == 10
        assert not cursor.has_more_now  # pyright: ignore[reportOptionalMemberAccess]
        assert cursor.log_key == [*log_key_prefix, "4"]  # pyright: ignore[reportOptionalMemberAccess]
        # processed up to the end of the file, but there is not another file to process so cursor should be -1
        assert cursor.line == -1  # pyright: ignore[reportOptionalMemberAccess]
        for ll in log_lines:
            assert ll == next(all_logs_iter)
