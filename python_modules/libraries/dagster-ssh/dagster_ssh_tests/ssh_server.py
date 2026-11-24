"""An in-process SSH server, and helpers that build resources to connect to it."""

import base64
import hashlib
import logging
import socket
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path

import paramiko
import pytest
from dagster._core.execution.context.init import build_init_resource_context
from dagster_ssh.resources import SSHResource, ssh_resource
from paramiko.common import AUTH_FAILED, AUTH_SUCCESSFUL, OPEN_SUCCEEDED


class PasswordServer(paramiko.ServerInterface):
    def __init__(self, auth_attempts: list[str], destinations: dict[int, tuple[str, int]]):
        self.auth_attempts = auth_attempts
        self.destinations = destinations

    def check_auth_password(self, username: str, password: str) -> int:
        self.auth_attempts.append(username)
        if (username, password) == ("user", "pw"):
            return AUTH_SUCCESSFUL
        return AUTH_FAILED

    def get_allowed_auths(self, username: str) -> str:
        return "password"

    def check_channel_direct_tcpip_request(
        self, chanid: int, origin: tuple[str, int], destination: tuple[str, int]
    ) -> int:
        self.destinations[chanid] = destination
        return OPEN_SUCCEEDED


def relay(channel: paramiko.Channel, destination: tuple[str, int]) -> None:
    """Forwards each request on a tunnel channel to its destination and sends back the reply."""
    with channel, socket.create_connection(destination) as upstream:
        while data := channel.recv(4096):
            upstream.sendall(data)
            channel.sendall(upstream.recv(4096))


class SSHServer:
    def __init__(self, host_key: paramiko.PKey):
        self.host_key = host_key
        self._listener = socket.create_server(("127.0.0.1", 0))
        self._listener.settimeout(0.1)
        self.port: int = self._listener.getsockname()[1]
        self._transports: list[paramiko.Transport] = []
        self.auth_attempts: list[str] = []
        self._destinations: dict[int, tuple[str, int]] = {}
        self._stopped = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    @property
    def known_hosts_name(self) -> str:
        return f"[127.0.0.1]:{self.port}"

    def _serve(self) -> None:
        while not self._stopped.is_set():
            try:
                sock, _ = self._listener.accept()
            except TimeoutError:
                continue
            transport = paramiko.Transport(sock)
            transport.add_server_key(self.host_key)
            transport.start_server(
                event=threading.Event(),
                server=PasswordServer(self.auth_attempts, self._destinations),
            )
            self._transports.append(transport)
            threading.Thread(target=self._forward, args=(transport,), daemon=True).start()

    def _forward(self, transport: paramiko.Transport) -> None:
        while transport.is_active():
            channel = transport.accept(timeout=0.1)
            if channel is not None:
                destination = self._destinations[channel.get_id()]
                threading.Thread(target=relay, args=(channel, destination), daemon=True).start()

    def stop(self) -> None:
        self._stopped.set()
        self._thread.join(timeout=5)
        self._listener.close()
        for transport in self._transports:
            transport.close()


def write_known_hosts(path: Path, hostname: str, *keys: paramiko.PKey) -> Path:
    """Writes one known_hosts line per key, keeping several keys of the same type."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{hostname} {key.get_name()} {key.get_base64()}\n" for key in keys]
    path.write_text("".join(lines), encoding="utf-8")
    return path


def write_revocation(path: Path, hosts: str, key: paramiko.PKey) -> Path:
    path.write_text(f"@revoked {hosts} {key.get_name()} {key.get_base64()}\n", encoding="utf-8")
    return path


# Relays stdin and stdout to the server, as `ssh -W` would for a ProxyCommand.
RELAY_SCRIPT = """
import socket, sys, threading
upstream = socket.create_connection(("127.0.0.1", int(sys.argv[1])))
def send():
    while data := sys.stdin.buffer.read1(65536):
        upstream.sendall(data)
threading.Thread(target=send, daemon=True).start()
while data := upstream.recv(65536):
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()
"""


def has_exited(proxy: paramiko.ProxyCommand) -> bool:
    try:
        proxy.process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        return False
    return True


def pythonic_resource(**config) -> SSHResource:
    resource = SSHResource(**config)
    resource.setup_for_execution(build_init_resource_context())
    resource.set_logger(logging.getLogger("test_host_key_verification"))
    return resource


def legacy_resource(**config) -> SSHResource:
    resource = ssh_resource(build_init_resource_context(config=config))
    resource.set_logger(logging.getLogger("test_host_key_verification"))
    return resource


ResourceBuilder = Callable[..., SSHResource]

builders = pytest.mark.parametrize("build", [pythonic_resource, legacy_resource])


def connection_config(server: SSHServer, **overrides) -> dict:
    return {
        "remote_host": "127.0.0.1",
        "remote_port": server.port,
        "username": "user",
        "password": "pw",
        **overrides,
    }


def sha256_fingerprint(key: paramiko.PKey) -> str:
    """The fingerprint as ``ssh-keygen -l`` prints it."""
    digest = base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode()
    return f"SHA256:{digest.rstrip('=')}"
