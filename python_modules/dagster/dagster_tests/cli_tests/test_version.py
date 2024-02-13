import subprocess

from dagster.version import __version__


def test_version():
    assert (
        subprocess.check_output(["dagster", "--version"]).decode("utf-8").strip()
        == f"dagster, version {__version__}"
    )
