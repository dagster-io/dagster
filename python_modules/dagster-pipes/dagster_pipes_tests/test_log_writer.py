import os
import sys
import tempfile

from dagster_pipes import (
    PipesDefaultLogWriter,
    PipesFileMessageWriterChannel,
    PipesStdioFileLogWriter,
)


def test_pipes_out_err_file_log_writer(capsys):
    with tempfile.TemporaryDirectory() as tempdir:
        with capsys.disabled(), PipesStdioFileLogWriter().open(
            {
                "logs_dir": tempdir,
            }
        ):
            print("Writing this to stdout")  # noqa
            print("And this to stderr", file=sys.stderr)  # noqa

        assert set(os.listdir(tempdir)) == {"stderr", "stdout"}

        with open(os.path.join(tempdir, "stdout"), "r") as stdout_file:
            contents = stdout_file.read()
            assert "Writing this to stdout" in contents

        with open(os.path.join(tempdir, "stderr"), "r") as stderr_file:
            contents = stderr_file.read()
            assert "And this to stderr" in contents


def test_pipes_default_log_writer(capsys):
    with tempfile.NamedTemporaryFile() as file:
        message_channel = PipesFileMessageWriterChannel(file.name)

        log_writer = PipesDefaultLogWriter()
        log_writer.message_channel = message_channel
        with capsys.disabled(), log_writer.open({}):
            print("Writing this to stdout")  # noqa
            print("And this to stderr", file=sys.stderr)  # noqa
        with open(file.name, "r") as log_file:
            messages = log_file.read().splitlines()
            assert (
                '{"__dagster_pipes_version": "0.1", "method": "report_custom_message", "params": {"stream": "stdout", "text": "Starting PipesDefaultLogWriterChannel(stdout)\\nStarting PipesDefaultLogWriterChannel(stderr)\\nWriting this to stdout\\nAnd this to stderr\\n"}}'
                in messages
            )
