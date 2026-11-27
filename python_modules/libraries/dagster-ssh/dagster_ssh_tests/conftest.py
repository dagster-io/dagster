"""Fixtures shared by the dagster-ssh tests."""

import sys
from collections.abc import Iterator
from pathlib import Path

import paramiko
import pytest

from dagster_ssh_tests.ssh_server import RELAY_SCRIPT, SSHServer, write_known_hosts


@pytest.fixture(autouse=True)
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Keeps the real ~/.ssh, /etc/ssh/ssh_known_hosts and SSH agent out of every test."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(
        "dagster_ssh.resources.SYSTEM_KNOWN_HOSTS_FILE", str(tmp_path / "ssh_known_hosts")
    )
    monkeypatch.delenv("SSH_AUTH_SOCK", raising=False)
    return home


@pytest.fixture
def server() -> Iterator[SSHServer]:
    server = SSHServer(paramiko.ECDSAKey.generate())
    yield server
    server.stop()


@pytest.fixture
def proxy_commands(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[paramiko.ProxyCommand]]:
    """Every ProxyCommand started during the test."""
    started: list[paramiko.ProxyCommand] = []

    class RecordedProxyCommand(paramiko.ProxyCommand):
        def __init__(self, command_line: str):
            super().__init__(command_line)
            started.append(self)

    monkeypatch.setattr(paramiko, "ProxyCommand", RecordedProxyCommand)
    yield started
    for proxy in started:
        proxy.process.kill()
        proxy.process.wait()


@pytest.fixture
def gateway(server: SSHServer, home: Path, tmp_path: Path) -> str:
    """A known host, named in ~/.ssh/config, that is reached through a ProxyCommand."""
    relay = tmp_path / "relay.py"
    relay.write_text(RELAY_SCRIPT, encoding="utf-8")
    (home / ".ssh").mkdir()
    (home / ".ssh" / "config").write_text(
        f"Host gateway\n  ProxyCommand {sys.executable} {relay} {server.port}\n", encoding="utf-8"
    )
    write_known_hosts(home / ".ssh" / "known_hosts", "gateway", server.host_key)
    return "gateway"
