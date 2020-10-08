import logging
import os

import pytest
from dagster_shell.utils import execute, execute_script_file


def test_bad_output_logging():
    with pytest.raises(Exception, match="Unrecognized output_logging NOT_A_VALID_LOGGING_VALUE"):
        execute("ls", output_logging="NOT_A_VALID_LOGGING_VALUE", log=logging)


def test_execute_inline(tmp_file):
    with tmp_file("some file contents") as (tmp_path, tmp_file):
        res, retcode = execute("ls", cwd=tmp_path, output_logging="BUFFER", log=logging)
        assert os.path.basename(tmp_file) in res
        assert retcode == 0


def test_execute_file(tmp_file):
    with tmp_file("ls") as (tmp_path, tmp_file):
        res, retcode = execute_script_file(
            tmp_file, output_logging="BUFFER", log=logging, cwd=tmp_path
        )
        assert os.path.basename(tmp_file) in res
        assert retcode == 0


def test_env(tmp_file):
    cmd = "echo $TEST_VAR"
    res, retcode = execute(
        cmd, output_logging="BUFFER", log=logging, env={"TEST_VAR": "some_env_value"}
    )
    assert res.strip() == "some_env_value"
    assert retcode == 0

    with tmp_file(cmd) as (_, tmp_file):
        res, retcode = execute_script_file(
            tmp_file, output_logging="BUFFER", log=logging, env={"TEST_VAR": "some_env_value"},
        )
        assert res.strip() == "some_env_value"
        assert retcode == 0


def test_output_logging_stream(caplog):
    caplog.set_level(logging.INFO)

    _, retcode = execute("ls", output_logging="STREAM", log=logging)
    log_messages = [r.message for r in caplog.records]
    assert log_messages[0].startswith("Using temporary directory: ")
    assert log_messages[1].startswith("Temporary script location: ")
    assert log_messages[2] == "Running command:\nls"
    assert log_messages[3]
    assert retcode == 0

    caplog.clear()

    _, retcode = execute("ls", output_logging="STREAM", log=logging)
    log_messages = [r.message for r in caplog.records]
    assert log_messages[0].startswith("Using temporary directory: ")
    assert log_messages[1].startswith("Temporary script location: ")
    assert log_messages[2] == "Running command:\nls"
    assert log_messages[3]
    assert retcode == 0

    caplog.clear()

    _, retcode = execute(
        'for i in 1 2 3; do echo "iter $i"; done;', output_logging="STREAM", log=logging,
    )
    log_messages = [r.message for r in caplog.records]
    assert retcode == 0
    assert log_messages[3:6] == ["iter 1", "iter 2", "iter 3"]

    caplog.clear()

    _, retcode = execute(
        'for i in 1 2 3; do echo "iter $i"; done;', output_logging="BUFFER", log=logging,
    )
    log_messages = [r.message for r in caplog.records]
    assert retcode == 0
    assert log_messages[3] == "iter 1\niter 2\niter 3\n"
