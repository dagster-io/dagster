import logging
import os
import sys
import tempfile
from time import sleep

from dagster_pipes import PipesStdioFileLogWriter


def test_pipes_stdio_file_log_writer(capsys):
    logger = logging.getLogger("dagster-pipes")
    fh = logging.FileHandler("spam.log")
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    with tempfile.TemporaryDirectory() as tempdir:
        with capsys.disabled(), PipesStdioFileLogWriter().open(
            {
                "logs_dir": tempdir,
            }
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
            with open(os.path.join(tempdir, stream), "r") as stdout_file:
                contents = stdout_file.read()
                for i in range(1, 4):
                    assert f"Writing this to {stream} {i}" in contents

                assert f"This {stream} is not captured" not in contents
