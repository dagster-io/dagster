"""Host key verification for get_tunnel."""

import io
import socket
import sys
import threading
from collections.abc import Iterator
from pathlib import Path

import paramiko
import pytest
from dagster_ssh.host_keys import (
    HostKeyRejectedError,
    KnownHostsTransport,
    KnownHostTunnelForwarder,
)
from dagster_ssh.known_hosts import KnownHostKeys
from dagster_ssh.resources import SSHResource
from sshtunnel import BaseSSHTunnelForwarderError, SSHTunnelForwarder

from dagster_ssh_tests.ssh_server import (
    RELAY_SCRIPT,
    ResourceBuilder,
    SSHServer,
    builders,
    connection_config,
    has_exited,
    pythonic_resource,
    sha256_fingerprint,
    write_known_hosts,
    write_revocation,
)


@pytest.fixture
def echo_port() -> Iterator[int]:
    """A local TCP server that sends back whatever it receives, for tunnels to forward to."""
    listener = socket.create_server(("127.0.0.1", 0))
    listener.settimeout(0.1)
    stopped = threading.Event()

    def echo(conn: socket.socket) -> None:
        with conn:
            while data := conn.recv(4096):
                conn.sendall(data)

    def serve() -> None:
        while not stopped.is_set():
            try:
                conn, _ = listener.accept()
            except TimeoutError:
                continue
            threading.Thread(target=echo, args=(conn,), daemon=True).start()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    yield listener.getsockname()[1]
    stopped.set()
    thread.join(timeout=5)
    listener.close()


def round_trip(tunnel: SSHTunnelForwarder, payload: bytes) -> bytes:
    with socket.create_connection(("localhost", tunnel.local_bind_port), timeout=5) as conn:
        conn.sendall(payload)
        return conn.recv(len(payload))


@builders
def test_tunnel_to_unknown_host_is_rejected_before_authentication(
    server: SSHServer, build: ResourceBuilder, echo_port: int
) -> None:
    resource = build(**connection_config(server))

    with pytest.raises(paramiko.SSHException) as excinfo:
        resource.get_tunnel(echo_port, remote_host="127.0.0.1")

    message = str(excinfo.value)
    assert server.known_hosts_name in message
    assert "no_host_key_check" in message
    assert server.auth_attempts == []


@pytest.fixture(params=["known_hosts_file", "user_known_hosts"])
def trusting_config(
    request: pytest.FixtureRequest, server: SSHServer, home: Path, tmp_path: Path
) -> dict:
    """Connection config for a resource that trusts the server's key, from either source."""
    if request.param == "user_known_hosts":
        write_known_hosts(home / ".ssh" / "known_hosts", server.known_hosts_name, server.host_key)
        return connection_config(server)
    known_hosts = write_known_hosts(
        tmp_path / "known_hosts", server.known_hosts_name, server.host_key
    )
    return connection_config(server, known_hosts_file=str(known_hosts))


@builders
def test_tunnel_to_known_host_forwards(
    server: SSHServer, build: ResourceBuilder, echo_port: int, trusting_config: dict
) -> None:
    resource = build(**trusting_config)

    with resource.get_tunnel(echo_port, remote_host="127.0.0.1") as tunnel:
        assert round_trip(tunnel, b"ping") == b"ping"

    assert server.auth_attempts == ["user"]


def test_tunnel_accepts_host_trusted_under_a_later_key_type(
    server: SSHServer, echo_port: int, tmp_path: Path
) -> None:
    known_hosts = write_known_hosts(
        tmp_path / "known_hosts",
        server.known_hosts_name,
        paramiko.RSAKey.generate(2048),
        server.host_key,
    )
    resource = pythonic_resource(**connection_config(server, known_hosts_file=str(known_hosts)))

    with resource.get_tunnel(echo_port, remote_host="127.0.0.1") as tunnel:
        assert round_trip(tunnel, b"ping") == b"ping"


def test_tunnel_accepts_host_listed_with_several_keys_of_one_type(
    server: SSHServer, echo_port: int, tmp_path: Path
) -> None:
    known_hosts = write_known_hosts(
        tmp_path / "known_hosts",
        server.known_hosts_name,
        paramiko.ECDSAKey.generate(),
        server.host_key,
    )
    resource = pythonic_resource(**connection_config(server, known_hosts_file=str(known_hosts)))

    with resource.get_tunnel(echo_port, remote_host="127.0.0.1") as tunnel:
        assert round_trip(tunnel, b"ping") == b"ping"


def test_tunnel_accepts_host_under_hashed_name(
    server: SSHServer, echo_port: int, tmp_path: Path
) -> None:
    hashed_name = paramiko.HostKeys.hash_host(server.known_hosts_name)
    known_hosts = write_known_hosts(tmp_path / "known_hosts", hashed_name, server.host_key)
    resource = pythonic_resource(**connection_config(server, known_hosts_file=str(known_hosts)))

    with resource.get_tunnel(echo_port, remote_host="127.0.0.1") as tunnel:
        assert round_trip(tunnel, b"ping") == b"ping"


def test_tunnel_looks_up_host_and_port_from_ssh_config(
    server: SSHServer, echo_port: int, home: Path, tmp_path: Path
) -> None:
    (home / ".ssh").mkdir()
    (home / ".ssh" / "config").write_text(
        f"Host gateway\n  HostName 127.0.0.1\n  Port {server.port}\n"
    )
    known_hosts = write_known_hosts(
        tmp_path / "known_hosts", server.known_hosts_name, server.host_key
    )
    resource = pythonic_resource(
        remote_host="gateway", username="user", password="pw", known_hosts_file=str(known_hosts)
    )

    with resource.get_tunnel(echo_port, remote_host="127.0.0.1") as tunnel:
        assert round_trip(tunnel, b"ping") == b"ping"


def test_unknown_host_is_rejected_before_sshtunnel_loads_keys(
    server: SSHServer, echo_port: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    def load_keys(*args, **kwargs):
        raise AssertionError("sshtunnel loaded keys for a host that is not in known_hosts")

    monkeypatch.setattr(SSHTunnelForwarder, "_consolidate_auth", staticmethod(load_keys))
    resource = pythonic_resource(**connection_config(server))

    with pytest.raises(paramiko.SSHException, match="is not in known_hosts"):
        resource.get_tunnel(echo_port, remote_host="127.0.0.1")


def test_known_hosts_transport_rejects_asynchronous_start(server: SSHServer) -> None:
    transport = KnownHostsTransport(socket.create_connection(("127.0.0.1", server.port)))

    with pytest.raises(ValueError, match="event"):
        transport.start_client(event=threading.Event())

    assert not transport.is_active()
    transport.close()


@pytest.mark.parametrize(
    "known_key",
    [paramiko.ECDSAKey.generate(), paramiko.RSAKey.generate(2048)],
    ids=["same_key_type", "other_key_type"],
)
def test_tunnel_to_host_with_changed_key_is_rejected_before_authentication(
    server: SSHServer, echo_port: int, tmp_path: Path, known_key: paramiko.PKey
) -> None:
    known_hosts = write_known_hosts(tmp_path / "known_hosts", server.known_hosts_name, known_key)
    resource = pythonic_resource(**connection_config(server, known_hosts_file=str(known_hosts)))
    tunnel = resource.get_tunnel(echo_port, remote_host="127.0.0.1")

    with pytest.raises(HostKeyRejectedError) as excinfo:
        tunnel.start()

    message = str(excinfo.value)
    assert server.known_hosts_name in message
    assert sha256_fingerprint(server.host_key) in message
    assert server.auth_attempts == []


@builders
def test_tunnel_without_host_key_check_forwards(
    server: SSHServer, build: ResourceBuilder, echo_port: int
) -> None:
    resource = build(**connection_config(server, no_host_key_check=True))

    with resource.get_tunnel(echo_port, remote_host="127.0.0.1") as tunnel:
        assert round_trip(tunnel, b"ping") == b"ping"


def test_tunnel_connection_failure_raises_tunnel_error(
    server: SSHServer, echo_port: int, tmp_path: Path
) -> None:
    with socket.create_server(("127.0.0.1", 0)) as unused:
        closed_port = unused.getsockname()[1]
    known_hosts = write_known_hosts(
        tmp_path / "known_hosts", f"[127.0.0.1]:{closed_port}", server.host_key
    )
    resource = pythonic_resource(
        remote_host="127.0.0.1",
        remote_port=closed_port,
        username="user",
        password="pw",
        known_hosts_file=str(known_hosts),
    )
    tunnel = resource.get_tunnel(echo_port, remote_host="127.0.0.1")

    with pytest.raises(BaseSSHTunnelForwarderError, match="Could not establish session"):
        tunnel.start()


def test_tunnel_without_host_key_check_still_rejects_changed_key(
    server: SSHServer, echo_port: int, tmp_path: Path
) -> None:
    known_hosts = write_known_hosts(
        tmp_path / "known_hosts", server.known_hosts_name, paramiko.ECDSAKey.generate()
    )
    resource = pythonic_resource(
        **connection_config(server, no_host_key_check=True, known_hosts_file=str(known_hosts))
    )
    tunnel = resource.get_tunnel(echo_port, remote_host="127.0.0.1")

    with pytest.raises(HostKeyRejectedError, match="does not match"):
        tunnel.start()

    assert server.auth_attempts == []


def test_tunnel_rejects_revoked_key_before_authentication(
    server: SSHServer, echo_port: int, tmp_path: Path
) -> None:
    key = server.host_key
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text(f"@revoked * {key.get_name()} {key.get_base64()}\n")
    resource = pythonic_resource(
        **connection_config(server, no_host_key_check=True, known_hosts_file=str(known_hosts))
    )
    tunnel = resource.get_tunnel(echo_port, remote_host="127.0.0.1")

    with pytest.raises(HostKeyRejectedError, match="revoked"):
        tunnel.start()

    assert server.auth_attempts == []


def test_tunnel_presenting_revoked_key_is_rejected_as_revoked(
    server: SSHServer, echo_port: int, tmp_path: Path
) -> None:
    known_hosts = write_revocation(
        tmp_path / "known_hosts", server.known_hosts_name, server.host_key
    )
    resource = pythonic_resource(**connection_config(server, known_hosts_file=str(known_hosts)))
    tunnel = resource.get_tunnel(echo_port, remote_host="127.0.0.1")

    with pytest.raises(HostKeyRejectedError, match="@revoked") as excinfo:
        tunnel.start()

    assert "To trust this host" not in str(excinfo.value)
    assert server.auth_attempts == []


def test_tunnel_to_host_matched_only_by_a_wildcard_revocation_is_rejected_as_unknown(
    server: SSHServer, echo_port: int, tmp_path: Path
) -> None:
    known_hosts = write_revocation(tmp_path / "known_hosts", "*", paramiko.ECDSAKey.generate())
    resource = pythonic_resource(**connection_config(server, known_hosts_file=str(known_hosts)))
    tunnel = resource.get_tunnel(echo_port, remote_host="127.0.0.1")

    with pytest.raises(HostKeyRejectedError, match="not in known_hosts") as excinfo:
        tunnel.start()

    assert "To trust this host" in str(excinfo.value)
    assert server.auth_attempts == []


def private_key_string(key: paramiko.RSAKey) -> str:
    buffer = io.StringIO()
    key.write_private_key(buffer)
    return buffer.getvalue()


def test_tunnel_through_proxy_command_tries_each_credential_and_restarts(
    gateway: str,
    echo_port: int,
    proxy_commands: list[paramiko.ProxyCommand],
) -> None:
    # The server accepts only the password, so the key fails first and closes its transport.
    resource = SSHResource(
        remote_host=gateway,
        username="user",
        password="pw",
        key_string=private_key_string(paramiko.RSAKey.generate(2048)),
    )
    tunnel = resource.get_tunnel(echo_port, remote_host="127.0.0.1")

    tunnel.start()
    assert round_trip(tunnel, b"ping") == b"ping"
    tunnel.stop()
    tunnel.start()
    assert round_trip(tunnel, b"pong") == b"pong"
    tunnel.stop()

    # One transport for the key and one for the password, on each start.
    assert len(proxy_commands) == 4
    assert all(has_exited(proxy) for proxy in proxy_commands)


def test_tunnel_that_is_never_started_starts_no_proxy_command(
    gateway: str, echo_port: int, proxy_commands: list[paramiko.ProxyCommand]
) -> None:
    resource = SSHResource(remote_host=gateway, username="user", password="pw")

    resource.get_tunnel(echo_port, remote_host="127.0.0.1")

    assert proxy_commands == []


def test_tunnel_to_unknown_host_through_proxy_command_starts_none(
    gateway: str, home: Path, echo_port: int, proxy_commands: list[paramiko.ProxyCommand]
) -> None:
    (home / ".ssh" / "known_hosts").unlink()
    resource = SSHResource(remote_host=gateway, username="user", password="pw")

    with pytest.raises(paramiko.SSHException, match="is not in known_hosts"):
        resource.get_tunnel(echo_port, remote_host="127.0.0.1")

    assert proxy_commands == []


@pytest.fixture
def relay_command(server: SSHServer, tmp_path: Path) -> str:
    relay = tmp_path / "relay.py"
    relay.write_text(RELAY_SCRIPT, encoding="utf-8")
    return f"{sys.executable} {relay} {server.port}"


def any_host_key(entry: str) -> KnownHostKeys:
    return KnownHostKeys(known=[], revoked=[])


def forwarder(server: SSHServer, echo_port: int, **kwargs) -> KnownHostTunnelForwarder:
    return KnownHostTunnelForwarder(
        "127.0.0.1",
        ssh_port=server.port,
        known_host_keys=any_host_key,
        accept_unknown=True,
        ssh_username="user",
        ssh_password="pw",
        remote_bind_address=("127.0.0.1", echo_port),
        **kwargs,
    )


@pytest.mark.parametrize(
    "options",
    [{"ssh_proxy_enabled": False}, {"ssh_config_file": None}],
    ids=["proxy_disabled", "no_config_file"],
)
def test_tunnel_forwarder_starts_no_proxy_command_when_told_not_to(
    server: SSHServer,
    echo_port: int,
    home: Path,
    relay_command: str,
    proxy_commands: list[paramiko.ProxyCommand],
    options: dict,
) -> None:
    (home / ".ssh").mkdir()
    (home / ".ssh" / "config").write_text(
        f"Host 127.0.0.1\n  ProxyCommand {relay_command}\n", encoding="utf-8"
    )

    with forwarder(server, echo_port, **options) as tunnel:
        assert round_trip(tunnel, b"ping") == b"ping"

    assert proxy_commands == []


def test_tunnel_forwarder_reads_proxy_command_from_its_ssh_config_file(
    server: SSHServer,
    echo_port: int,
    tmp_path: Path,
    relay_command: str,
    proxy_commands: list[paramiko.ProxyCommand],
) -> None:
    config_file = tmp_path / "ssh_config"
    config_file.write_text(f"Host 127.0.0.1\n  ProxyCommand {relay_command}\n", encoding="utf-8")

    with forwarder(server, echo_port, ssh_config_file=str(config_file)) as tunnel:
        assert round_trip(tunnel, b"ping") == b"ping"

    assert len(proxy_commands) == 1
    assert all(has_exited(proxy) for proxy in proxy_commands)


# Answers with an SSH 1.0 banner, which paramiko rejects before key exchange, and stays running.
NOT_SSH_2 = (
    "import sys, time; sys.stdout.write('SSH-1.0-old\\r\\n'); sys.stdout.flush(); time.sleep(60)"
)


def test_failed_tunnel_handshake_leaves_no_proxy_command_running(
    home: Path, echo_port: int, proxy_commands: list[paramiko.ProxyCommand]
) -> None:
    (home / ".ssh").mkdir()
    (home / ".ssh" / "config").write_text(
        f'Host old\n  ProxyCommand {sys.executable} -c "{NOT_SSH_2}"\n', encoding="utf-8"
    )
    resource = SSHResource(
        remote_host="old", username="user", password="pw", no_host_key_check=True
    )
    tunnel = resource.get_tunnel(echo_port, remote_host="127.0.0.1")

    with pytest.raises(BaseSSHTunnelForwarderError):
        tunnel.start()

    assert len(proxy_commands) == 1
    assert all(has_exited(proxy) for proxy in proxy_commands)
