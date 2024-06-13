from dagster._core.definitions.instigation_logger import InstigationLogger


def test_gets_correct_logger():
    custom_logger_name = "foo"

    instigation_logger = InstigationLogger()
    assert instigation_logger.name == "dagster"

    instigation_logger = InstigationLogger(logger_name=custom_logger_name)
    assert instigation_logger.name == custom_logger_name
