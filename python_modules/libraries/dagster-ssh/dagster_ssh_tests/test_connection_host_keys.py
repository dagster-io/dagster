"""Host key verification for direct connections: get_connection, sftp_get and sftp_put."""

import logging
import os
from collections.abc import Callable
from pathlib import Path

import paramiko
import pytest
from dagster_ssh.resources import SSHResource

from dagster_ssh_tests.ssh_server import (
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


@builders
def test_unknown_host_is_rejected_by_default(server: SSHServer, build: ResourceBuilder) -> None:
    resource = build(**connection_config(server))

    with pytest.raises(paramiko.SSHException) as excinfo:
        resource.get_connection()

    message = str(excinfo.value)
    assert server.known_hosts_name in message
    assert server.host_key.get_name() in message
    assert sha256_fingerprint(server.host_key) in message
    assert "no_host_key_check" in message


def is_authenticated(client: paramiko.SSHClient) -> bool:
    transport = client.get_transport()
    return transport is not None and transport.is_authenticated()


@builders
def test_host_in_known_hosts_file_is_accepted(
    server: SSHServer, build: ResourceBuilder, tmp_path: Path
) -> None:
    known_hosts = write_known_hosts(
        tmp_path / "known_hosts", server.known_hosts_name, server.host_key
    )
    resource = build(**connection_config(server, known_hosts_file=str(known_hosts)))

    client = resource.get_connection()

    assert is_authenticated(client)
    client.close()


def test_host_in_user_known_hosts_is_accepted(server: SSHServer, home: Path) -> None:
    write_known_hosts(home / ".ssh" / "known_hosts", server.known_hosts_name, server.host_key)
    resource = pythonic_resource(**connection_config(server))

    client = resource.get_connection()

    assert is_authenticated(client)
    client.close()


@pytest.mark.parametrize("allow_host_key_change", [False, True])
def test_changed_host_key_is_rejected(
    server: SSHServer, tmp_path: Path, allow_host_key_change: bool
) -> None:
    known_hosts = write_known_hosts(
        tmp_path / "known_hosts", server.known_hosts_name, paramiko.ECDSAKey.generate()
    )
    resource = pythonic_resource(
        **connection_config(
            server,
            known_hosts_file=str(known_hosts),
            allow_host_key_change=allow_host_key_change,
        )
    )

    with pytest.raises(paramiko.BadHostKeyException):
        resource.get_connection()


@builders
def test_no_host_key_check_connects_without_saving_keys(
    server: SSHServer, build: ResourceBuilder, home: Path, tmp_path: Path
) -> None:
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text("")
    resource = build(
        **connection_config(server, no_host_key_check=True, known_hosts_file=str(known_hosts))
    )

    client = resource.get_connection()

    assert is_authenticated(client)
    client.close()
    assert not (home / ".ssh").exists()
    assert known_hosts.read_text() == ""


@pytest.fixture(params=["system", "user", "known_hosts_file"])
def known_hosts_source(
    request: pytest.FixtureRequest, home: Path, tmp_path: Path
) -> tuple[Path, dict]:
    """A known_hosts path the resource reads, and the config overrides that make it read it."""
    if request.param == "system":
        return tmp_path / "ssh_known_hosts", {}
    if request.param == "user":
        return home / ".ssh" / "known_hosts", {}
    path = tmp_path / "known_hosts"
    return path, {"known_hosts_file": str(path)}


@pytest.mark.parametrize("marker", ["@cert-authority", "@revoked"])
@pytest.mark.parametrize("no_host_key_check", [False, True])
def test_marker_lines_for_another_host_do_not_block_connection(
    server: SSHServer,
    known_hosts_source: tuple[Path, dict],
    marker: str,
    no_host_key_check: bool,
) -> None:
    path, overrides = known_hosts_source
    write_known_hosts(path, server.known_hosts_name, server.host_key)
    other_key = paramiko.RSAKey.generate(2048)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{marker} other.example.com ssh-rsa {other_key.get_base64()}\n")
    resource = pythonic_resource(
        **connection_config(server, no_host_key_check=no_host_key_check, **overrides)
    )

    client = resource.get_connection()

    assert is_authenticated(client)
    client.close()


def test_revoked_key_is_rejected_even_when_listed_as_known(
    server: SSHServer, known_hosts_source: tuple[Path, dict]
) -> None:
    path, overrides = known_hosts_source
    write_known_hosts(path, server.known_hosts_name, server.host_key)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"@revoked * {server.host_key.get_name()} {server.host_key.get_base64()}\n")
    resource = pythonic_resource(**connection_config(server, **overrides))

    with pytest.raises(paramiko.SSHException):
        resource.get_connection()

    assert server.auth_attempts == []


def several_keys_of_one_type(server: SSHServer) -> str:
    return (
        f"{server.known_hosts_name} ecdsa-sha2-nistp256 {paramiko.ECDSAKey.generate().get_base64()}\n"
        f"{server.known_hosts_name} {server.host_key.get_name()} {server.host_key.get_base64()}\n"
    )


def wildcard_pattern(server: SSHServer) -> str:
    return (
        f"[127.0.0.?]:{server.port} {server.host_key.get_name()} {server.host_key.get_base64()}\n"
    )


@pytest.mark.parametrize("known_hosts_text", [several_keys_of_one_type, wildcard_pattern])
def test_connection_matches_known_hosts_as_openssh_does(
    server: SSHServer, tmp_path: Path, known_hosts_text: Callable[[SSHServer], str]
) -> None:
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text(known_hosts_text(server), encoding="utf-8")
    resource = pythonic_resource(**connection_config(server, known_hosts_file=str(known_hosts)))

    client = resource.get_connection()

    assert is_authenticated(client)
    client.close()


def make_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir()


def make_unreadable_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    path.chmod(0)


@pytest.mark.parametrize(
    "make_unreadable",
    [
        make_directory,
        pytest.param(
            make_unreadable_file,
            marks=pytest.mark.skipif(os.geteuid() == 0, reason="root can read a mode-0 file"),
        ),
    ],
)
def test_no_host_key_check_skips_unreadable_known_hosts(
    server: SSHServer,
    known_hosts_source: tuple[Path, dict],
    make_unreadable: Callable[[Path], None],
) -> None:
    path, overrides = known_hosts_source
    make_unreadable(path)
    resource = pythonic_resource(**connection_config(server, no_host_key_check=True, **overrides))

    client = resource.get_connection()

    assert is_authenticated(client)
    client.close()


@builders
def test_no_host_key_check_still_rejects_changed_key(
    server: SSHServer, build: ResourceBuilder, tmp_path: Path
) -> None:
    known_hosts = write_known_hosts(
        tmp_path / "known_hosts", server.known_hosts_name, paramiko.ECDSAKey.generate()
    )
    resource = build(
        **connection_config(server, no_host_key_check=True, known_hosts_file=str(known_hosts))
    )

    with pytest.raises(paramiko.BadHostKeyException):
        resource.get_connection()

    assert server.auth_attempts == []


def test_no_host_key_check_still_rejects_revoked_key(server: SSHServer, tmp_path: Path) -> None:
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text(
        f"@revoked * {server.host_key.get_name()} {server.host_key.get_base64()}\n"
    )
    resource = pythonic_resource(
        **connection_config(server, no_host_key_check=True, known_hosts_file=str(known_hosts))
    )

    with pytest.raises(paramiko.SSHException, match="revoked"):
        resource.get_connection()

    assert server.auth_attempts == []


def test_changed_key_error_names_the_known_key_of_the_same_type(
    server: SSHServer, tmp_path: Path
) -> None:
    known_ecdsa_key = paramiko.ECDSAKey.generate()
    known_hosts = write_known_hosts(
        tmp_path / "known_hosts",
        server.known_hosts_name,
        paramiko.RSAKey.generate(2048),
        known_ecdsa_key,
    )
    resource = pythonic_resource(**connection_config(server, known_hosts_file=str(known_hosts)))

    with pytest.raises(paramiko.BadHostKeyException) as excinfo:
        resource.get_connection()

    assert excinfo.value.expected_key.asbytes() == known_ecdsa_key.asbytes()


@pytest.mark.parametrize("revoked_for", ["the_host", "every_host"])
def test_presented_revoked_key_is_rejected_as_revoked(
    server: SSHServer, tmp_path: Path, revoked_for: str
) -> None:
    hosts = server.known_hosts_name if revoked_for == "the_host" else "*"
    known_hosts = write_revocation(tmp_path / "known_hosts", hosts, server.host_key)
    resource = pythonic_resource(**connection_config(server, known_hosts_file=str(known_hosts)))

    with pytest.raises(paramiko.SSHException, match="@revoked") as excinfo:
        resource.get_connection()

    assert "To trust this host" not in str(excinfo.value)


@pytest.mark.parametrize("revoked_for", ["the_host", "every_host"])
def test_host_with_only_an_unrelated_revoked_key_is_rejected_as_unknown(
    server: SSHServer, tmp_path: Path, revoked_for: str
) -> None:
    hosts = server.known_hosts_name if revoked_for == "the_host" else "*"
    known_hosts = write_revocation(tmp_path / "known_hosts", hosts, paramiko.ECDSAKey.generate())
    resource = pythonic_resource(**connection_config(server, known_hosts_file=str(known_hosts)))

    with pytest.raises(paramiko.SSHException, match="not in known_hosts") as excinfo:
        resource.get_connection()

    assert "To trust this host" in str(excinfo.value)


def test_resource_without_setup_warns_about_no_host_key_check(
    server: SSHServer, caplog: pytest.LogCaptureFixture
) -> None:
    resource = SSHResource(**connection_config(server, no_host_key_check=True))

    with caplog.at_level(logging.WARNING):
        client = resource.get_connection()

    assert is_authenticated(client)
    client.close()
    assert "no_host_key_check=True" in caplog.text


def test_connection_through_proxy_command_leaves_no_process_running(
    gateway: str, proxy_commands: list[paramiko.ProxyCommand]
) -> None:
    resource = SSHResource(remote_host=gateway, username="user", password="pw")

    client = resource.get_connection()
    assert is_authenticated(client)
    client.close()

    assert len(proxy_commands) == 1
    assert all(has_exited(proxy) for proxy in proxy_commands)


def test_failed_connection_through_proxy_command_leaves_no_process_running(
    gateway: str, proxy_commands: list[paramiko.ProxyCommand]
) -> None:
    resource = SSHResource(remote_host=gateway, username="user", password="wrong")

    with pytest.raises(paramiko.AuthenticationException):
        resource.get_connection()

    assert len(proxy_commands) == 1
    assert all(has_exited(proxy) for proxy in proxy_commands)


def test_failed_connection_raises_its_own_error_when_closing_the_proxy_fails(
    gateway: str,
    proxy_commands: list[paramiko.ProxyCommand],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    close = paramiko.proxy.ProxyCommand.close
    closed: list[paramiko.ProxyCommand] = []

    def close_then_deny(proxy: paramiko.ProxyCommand) -> None:
        # Windows refuses to terminate a process that has already exited.
        if any(proxy is done for done in closed):
            raise PermissionError(5, "Access is denied")
        closed.append(proxy)
        close(proxy)

    monkeypatch.setattr(paramiko.proxy.ProxyCommand, "close", close_then_deny)
    resource = SSHResource(remote_host=gateway, username="user", password="wrong")

    with pytest.raises(paramiko.AuthenticationException):
        resource.get_connection()

    assert all(has_exited(proxy) for proxy in proxy_commands)
