import os
import sys
import tempfile
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any

import pytest
from dagster import job, op
from dagster._core.events import DagsterEventType
from dagster._core.storage.compute_log_manager import CapturedLogContext, ComputeIOType
from dagster._core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster._core.test_utils import instance_for_test
from dagster._serdes import ConfigurableClassData
from dagster._time import get_current_datetime
from typing_extensions import Self

from dagster_tests.storage_tests.utils.compute_log_manager import TestComputeLogManager


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
