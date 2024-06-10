import logging

from dagster._core.definitions.instigation_logger import InstigationLogger


def test_gets_correct_logger(caplog):
    custom_logger_name = "foo"
    caplog.set_level(logging.INFO, logger=custom_logger_name)

    instigation_logger = InstigationLogger()
    assert instigation_logger.name == "dagster"

    instigation_logger = InstigationLogger(logger_name=custom_logger_name)
    assert instigation_logger.name == custom_logger_name

    # name parameter is passed to metadata
    instigation_logger = InstigationLogger(name="bar", logger_name=custom_logger_name)
    assert instigation_logger.name == custom_logger_name
    assert instigation_logger._name == "bar"  # noqa: SLF001

    instigation_logger.info("this is a test message")

    assert len(caplog.records) == 1
