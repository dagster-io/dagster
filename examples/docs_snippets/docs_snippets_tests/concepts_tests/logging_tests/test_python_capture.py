from dagster.core.test_utils import instance_for_test
from docs_snippets.concepts.logging.python_logger import (
    scope_logged_job,
    scope_logged_job2,
)


def test_captured_python_logger_config(capsys):
    with instance_for_test(
        overrides={"python_logs": {"managed_python_loggers": ["root"]}}
    ) as instance:
        scope_logged_job().execute_in_process(instance=instance)
        captured = capsys.readouterr()
        assert "ambitious_op - Couldn't divide by zero!" in captured.err


def test_captured_python_logger_builtin(capsys):
    scope_logged_job2().execute_in_process()
    captured = capsys.readouterr()
    assert "ambitious_op - Couldn't divide by zero!" in captured.err
