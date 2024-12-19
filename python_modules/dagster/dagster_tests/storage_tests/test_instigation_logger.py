from contextlib import contextmanager
from unittest import mock

from dagster._core.definitions.instigation_logger import InstigationLogger
from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster._core.test_utils import instance_for_test


def test_gets_correct_logger():
    custom_logger_name = "foo"

    instigation_logger = InstigationLogger()
    assert instigation_logger.name == "dagster"

    instigation_logger = InstigationLogger(logger_name=custom_logger_name)
    assert instigation_logger.name == custom_logger_name


class CrashyStartupComputeLogManager(NoOpComputeLogManager):
    @contextmanager
    def open_log_stream(self, log_key, io_type):
        raise Exception("OOPS")
        yield None


class MockLogStreamComputeLogManager(NoOpComputeLogManager):
    @contextmanager
    def open_log_stream(self, log_key, io_type):
        yield mock.MagicMock()
        raise Exception("OOPS ON EXIT")


def test_instigation_logger_start_failure(capsys):
    with instance_for_test(
        overrides={
            "compute_logs": {
                "module": "dagster_tests.storage_tests.test_instigation_logger",
                "class": "CrashyStartupComputeLogManager",
            }
        }
    ) as instance:
        with InstigationLogger(log_key="foo", instance=instance) as logger:
            captured = capsys.readouterr()
            assert (
                captured.err.count("Exception initializing logger write stream: Exception: OOPS")
                == 1
            )
            logger.info("I can log without failing")


def test_instigation_logger_log_failure(capsys):
    with instance_for_test(
        overrides={
            "compute_logs": {
                "module": "dagster_tests.storage_tests.test_instigation_logger",
                "class": "MockLogStreamComputeLogManager",
            }
        }
    ) as instance:
        with InstigationLogger(log_key="foo", instance=instance) as logger:
            mock_write_stream = logger._capture_handler._write_stream  # type: ignore # noqa
            mock_write_stream.write.side_effect = Exception("OOPS")

            logger.info("HELLO")
            captured = capsys.readouterr()

            assert (
                captured.err.count("Exception writing to logger event stream: Exception: OOPS") == 1
            )

        captured = capsys.readouterr()

        assert (
            captured.err.count("Exception closing logger write stream: Exception: OOPS ON EXIT")
            == 1
        )
