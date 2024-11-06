import os
import sys
import tempfile

from dagster_pipes import PipesStdioFileLogWriter


def test_pipes_log_writer(capsys):
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
