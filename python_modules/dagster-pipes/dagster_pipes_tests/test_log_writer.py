import json
import os
import sys
import tempfile
from time import sleep

import pytest
from dagster_pipes import (
    DagsterPipesError,
    PipesDefaultLogWriter,
    PipesDefaultMessageWriter,
    PipesFileMessageWriterChannel,
    PipesStdioFileLogWriter,
    PipesStdioLogWriterChannel,
)


def test_pipes_stdio_file_log_writer(capsys):
    with tempfile.TemporaryDirectory() as tempdir:
        with (
            capsys.disabled(),
            PipesStdioFileLogWriter().open(
                {
                    "logs_dir": tempdir,
                }
            ),
        ):
            print(f"Writing this to stdout 1")  # noqa
            print(f"Writing this to stderr 1", file=sys.stderr)  # noqa

            sleep(1)

            print(f"Writing this to stdout 2")  # noqa
            print(f"Writing this to stderr 2", file=sys.stderr)  # noqa

            sleep(1)

            print("Writing this to stdout 3")  # noqa
            print("Writing this to stderr 3", file=sys.stderr)  # noqa

        print("This stdout is not captured")  # noqa
        print("This stderr is not captured", file=sys.stderr)  # noqa

        assert set(os.listdir(tempdir)) == {"stderr", "stdout"}

        for stream in ["stdout", "stderr"]:
            with open(os.path.join(tempdir, stream), encoding="utf-8") as stdout_file:
                contents = stdout_file.read()
                for i in range(1, 4):
                    assert f"Writing this to {stream} {i}" in contents


def test_pipes_default_log_writer(capsys):
    with tempfile.NamedTemporaryFile() as file:
        message_channel = PipesFileMessageWriterChannel(file.name)

        log_writer = PipesDefaultLogWriter(message_channel=message_channel)
        with (
            capsys.disabled(),
            log_writer.open({PipesDefaultMessageWriter.INCLUDE_STDIO_IN_MESSAGES_KEY: True}),
        ):
            print("Writing this to stdout")  # noqa
            print("And this to stderr", file=sys.stderr)  # noqa
        with open(file.name, encoding="utf-8") as log_file:
            messages = log_file.read().splitlines()

            # it's hard to make exact assertions here
            # since lines can be grouped in different ways

            # first, merge all messages from the same stream together

            stdout_text = ""
            stderr_text = ""

            for message in messages:
                params = json.loads(message)["params"]

                if params["stream"] == "stdout":
                    stdout_text += params["text"]
                elif params["stream"] == "stderr":
                    stderr_text += params["text"]
                else:
                    raise RuntimeError(f"Unexpected stream: {params['stream']}")

            assert "Writing this to stdout" in stdout_text
            assert "And this to stderr" in stderr_text


def test_default_writer_suggests_passing_a_writer_for_unknown_params():
    with pytest.raises(DagsterPipesError, match="pass it as `message_writer`"):
        with PipesDefaultMessageWriter().open({"bucket": "my-bucket"}):
            pass


def test_stdio_capture_closes_saved_file_descriptors(capsys, monkeypatch):
    saved_fds = []
    real_dup = os.dup

    def record_dup(fd):
        saved = real_dup(fd)
        saved_fds.append(saved)
        return saved

    monkeypatch.setattr(os, "dup", record_dup)
    monkeypatch.setattr(PipesStdioLogWriterChannel, "WAIT_FOR_TEE_SECONDS", 0.01)
    try:
        with tempfile.TemporaryDirectory() as tempdir:
            with (
                capsys.disabled(),
                PipesStdioFileLogWriter(interval=0.01).open({"logs_dir": tempdir}),
            ):
                pass
        assert len(saved_fds) == 2
        for fd in saved_fds:
            with pytest.raises(OSError):
                os.fstat(fd)
    finally:
        for fd in saved_fds:
            try:
                os.close(fd)
            except OSError:
                pass
