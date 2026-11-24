"""Reading ~/.ssh/config."""

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from dagster_ssh.ssh_config import resolve_ssh_config

from dagster_ssh_tests.ssh_server import pythonic_resource


def make_directory(path: Path) -> None:
    path.mkdir()


def make_unreadable_file(path: Path) -> None:
    path.write_text("Host *\n  Port 2222\n  IdentityFile ~/.ssh/other_key\n", encoding="utf-8")
    path.chmod(0)


@pytest.mark.parametrize(
    "make_config",
    [
        make_directory,
        pytest.param(
            make_unreadable_file,
            marks=pytest.mark.skipif(os.geteuid() == 0, reason="root can read a mode-0 file"),
        ),
    ],
)
def test_unreadable_ssh_config_is_skipped(home: Path, make_config: Callable[[Path], None]) -> None:
    (home / ".ssh").mkdir()
    make_config(home / ".ssh" / "config")

    assert resolve_ssh_config("gw.example.com", None) == ("gw.example.com", 22)
    resource = pythonic_resource(remote_host="gw.example.com", username="user")
    assert resource.key_file is None


@pytest.mark.skipif(
    sys.platform != "linux", reason="other platforms decode as UTF-8 under the C locale anyway"
)
def test_ssh_config_is_read_as_utf8_whatever_the_locale(home: Path) -> None:
    (home / ".ssh").mkdir()
    (home / ".ssh" / "config").write_text(
        "# caf\u00e9\nHost gw\n  HostName 10.0.0.5\n", encoding="utf-8"
    )
    ascii_locale = {**os.environ, "LC_ALL": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from dagster_ssh.ssh_config import resolve_ssh_config;"
            " print(resolve_ssh_config('gw', None))",
        ],
        env=ascii_locale,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.stdout.splitlines()[-1:] == ["('10.0.0.5', 22)"], result.stderr
