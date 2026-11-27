"""Reads ``~/.ssh/config`` the way sshtunnel does."""

import os

import paramiko
from paramiko.config import SSH_PORT, SSHConfigDict
from sshtunnel import SSH_CONFIG_FILE


def lookup_ssh_config(host: str, config_file: str | None = SSH_CONFIG_FILE) -> SSHConfigDict:
    """``config_file`` settings for ``host``. No file, or a missing or unreadable one, applies none."""
    path = os.path.expanduser(config_file) if config_file else None
    if path and os.path.isfile(path) and os.access(path, os.R_OK):
        # SSHConfig.from_path would decode with the locale's encoding.
        with open(path, encoding="utf-8") as f:
            return paramiko.SSHConfig.from_file(f).lookup(host)
    # Built directly: SSHConfig.lookup calls getpass.getuser(), which raises for a uid with no
    # passwd entry.
    return SSHConfigDict(hostname=host)


def resolve_ssh_config(
    host: str, port: int | None, config_file: str | None = SSH_CONFIG_FILE
) -> tuple[str, int]:
    """The host and port sshtunnel connects to after applying ``HostName`` and ``Port``."""
    info = lookup_ssh_config(host, config_file)
    return info["hostname"], int(port or info.get("port") or SSH_PORT)
