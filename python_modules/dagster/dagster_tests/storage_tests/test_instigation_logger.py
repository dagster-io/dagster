from contextlib import contextmanager
from unittest import mock

import dagster as dg
from dagster._core.definitions.instigation_logger import (
    InstigationLogger,
    get_instigation_log_records,
)
from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager


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
    with dg.instance_for_test(
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
    with dg.instance_for_test(
        overrides={
            "compute_logs": {
                "module": "dagster_tests.storage_tests.test_instigation_logger",
                "class": "MockLogStreamComputeLogManager",
            }
        }
    ) as instance:
        with InstigationLogger(log_key="foo", instance=instance) as logger:
            mock_write_stream = logger._capture_handler._write_stream  # type: ignore # noqa
            mock_write_stream.write.side_effect = Exception("OOPS")  # pyright: ignore[reportFunctionMemberAccess]

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


def test_instigation_logger_logs_weird_record_ok(capsys):
    class NonJsonSerializable:
        """A class that json.dumps doesn't know what to do with (by default)."""

        def __str__(self):
            return "non-jsonable-object"

    log_key = ["test-repo", "test-instigator", "123"]

    with dg.instance_for_test() as instance:  # pyright: ignore[reportAttributeAccessIssue]
        with InstigationLogger(
            log_key=log_key,
            instance=instance,
            repository_name="test-repo",
            instigator_name="test-instigator",
        ) as logger:
            logger.info("log without extras")
            logger.info("log with extras", extra={"non_json": NonJsonSerializable()})

            assert logger.has_captured_logs()

        captured = capsys.readouterr()

        assert "Exception initializing logger write stream" not in captured.err
        assert "Exception writing to logger event stream" not in captured.err
        assert "Exception closing logger write stream" not in captured.err
        assert "NonJsonSerializable is not JSON serializable" not in captured.err

        records = get_instigation_log_records(instance, log_key)

        assert len(records) >= 2
        assert "test-repo - test-instigator - log with extras" in {
            record.get("msg") for record in records if record.get("msg")
        }
        matching_records = [record for record in records if record.get("non_json")]
        assert matching_records and matching_records[0]["non_json"] == "non-jsonable-object"

        instance.compute_log_manager.delete_logs(log_key=log_key)
