import base64
import hashlib
from collections.abc import Callable, Iterable, Sequence

import paramiko
from paramiko.config import SSH_PORT
from sshtunnel import SSH_CONFIG_FILE, BaseSSHTunnelForwarderError, SSHTunnelForwarder

from dagster_ssh.known_hosts import KnownHostKeys
from dagster_ssh.ssh_config import lookup_ssh_config, resolve_ssh_config

TRUST_HOST_HINT = (
    "To trust this host, add its key to ~/.ssh/known_hosts (for example with `ssh-keyscan`), or"
    " set known_hosts_file to a file that contains it. Setting no_host_key_check=True accepts"
    " hosts that are not in known_hosts instead."
)


def sha256_fingerprint(key: paramiko.PKey) -> str:
    """The key's fingerprint as ``ssh-keygen -l`` prints it.

    Computed here because ``PKey.fingerprint`` only exists in paramiko 3.2 and later.
    """
    digest = base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode()
    return f"SHA256:{digest.rstrip('=')}"


def known_hosts_name(host: str, port: int) -> str:
    """The name known_hosts lists a host under, as ``paramiko.SSHClient`` looks it up."""
    return host if port == SSH_PORT else f"[{host}]:{port}"


def is_listed(key: paramiko.PKey, keys: Iterable[paramiko.PKey]) -> bool:
    return any(k.get_name() == key.get_name() and k.asbytes() == key.asbytes() for k in keys)


def preferred_key_types(available: Sequence[str], known: Iterable[str]) -> list[str]:
    """``available`` with the known key types first.

    The server then presents a key known_hosts lists whenever it has one, and still presents some
    key otherwise, so the mismatch error can name it.
    """
    wanted = []
    for key_type in known:
        wanted += (
            ["rsa-sha2-512", "rsa-sha2-256", key_type] if key_type == "ssh-rsa" else [key_type]
        )
    first = [key_type for key_type in dict.fromkeys(wanted) if key_type in available]
    return first + [key_type for key_type in available if key_type not in first]


class HostKeyRejectedError(BaseSSHTunnelForwarderError):
    """A tunnel's host presented a key that known_hosts does not trust.

    Not an ``SSHException``, because sshtunnel logs those and raises a generic "Could not
    establish session" error from ``start()`` instead.
    """


class KnownHostsTransport(paramiko.Transport):
    """A client transport that checks the server's key against known_hosts before authenticating.

    ``Transport.connect`` and ``SSHClient.connect`` authenticate right after ``start_client``
    returns, so the check runs there. A revoked key, or a key that differs from every key listed
    for the host, is always rejected; a host with no listed key is rejected unless
    ``accept_unknown`` is set.
    """

    known_hosts_entry: str
    host_keys: KnownHostKeys
    accept_unknown: bool

    def check_against(
        self, known_hosts_entry: str, host_keys: KnownHostKeys, accept_unknown: bool
    ) -> None:
        self.known_hosts_entry = known_hosts_entry
        self.host_keys = host_keys
        self.accept_unknown = accept_unknown

    def start_client(self, event=None, timeout=None):
        if event is not None:
            raise ValueError(
                "KnownHostsTransport checks the host key when start_client returns, so it does"
                " not support event"
            )
        options = self.get_security_options()
        options.key_types = preferred_key_types(
            options.key_types, (key.get_name() for key in self.host_keys.known)
        )
        try:
            super().start_client(timeout=timeout)
            self._check_host_key(self.get_remote_server_key())
        except Exception:
            self.close()
            raise

    def _check_host_key(self, presented: paramiko.PKey) -> None:
        described = (
            f"Host key verification failed: {self.known_hosts_entry} presented a"
            f" {presented.get_name()} key with fingerprint {sha256_fingerprint(presented)}"
        )
        if is_listed(presented, self.host_keys.revoked):
            raise self.rejected(f"{described}, which known_hosts marks @revoked.")
        if is_listed(presented, self.host_keys.known):
            return
        if self.host_keys.known:
            raise self.mismatched(
                presented,
                f"{described}, which does not match its known_hosts entry. If the host's key"
                " changed on purpose, replace its entry in known_hosts.",
            )
        if not self.accept_unknown:
            raise self.rejected(f"{described}, and it is not in known_hosts. {TRUST_HOST_HINT}")

    def rejected(self, message: str) -> Exception:
        return HostKeyRejectedError(message)

    def mismatched(self, presented: paramiko.PKey, message: str) -> Exception:
        return self.rejected(message)


class ClientKnownHostsTransport(KnownHostsTransport):
    """Raises the ``SSHException`` subclasses that ``SSHClient.connect`` callers already catch."""

    def rejected(self, message: str) -> Exception:
        return paramiko.SSHException(message)

    def mismatched(self, presented: paramiko.PKey, message: str) -> Exception:
        known = self.host_keys.known
        same_type = [key for key in known if key.get_name() == presented.get_name()]
        return paramiko.BadHostKeyException(
            self.known_hosts_entry, presented, (same_type or known)[0]
        )


class AcceptCheckedHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    """Accepts the key, which ``ClientKnownHostsTransport`` has already checked."""

    def missing_host_key(self, client, hostname, key):
        pass


def client_transport_factory(
    known_hosts_entry: str, host_keys: KnownHostKeys, accept_unknown: bool
) -> Callable[..., ClientKnownHostsTransport]:
    """A ``transport_factory`` for ``SSHClient.connect`` that checks the host key."""

    def build(*args, **kwargs) -> ClientKnownHostsTransport:
        transport = ClientKnownHostsTransport(*args, **kwargs)
        transport.check_against(known_hosts_entry, host_keys, accept_unknown)
        return transport

    return build


# Passed to sshtunnel's config reader in place of a proxy, so that it does not start the ssh
# config's ProxyCommand itself.
_NO_PROXY = object()


class KnownHostTunnelForwarder(SSHTunnelForwarder):
    """An ``SSHTunnelForwarder`` that verifies the host key against ``known_host_keys(entry)``.

    With ``accept_unknown``, a host with no known_hosts entry is accepted.
    """

    def __init__(
        self,
        ssh_address_or_host: str,
        *,
        ssh_port: int | None,
        known_host_keys: Callable[[str], KnownHostKeys],
        accept_unknown: bool,
        **kwargs,
    ):
        self._known_host_keys = known_host_keys
        self._accept_unknown = accept_unknown
        config_file = kwargs.get("ssh_config_file", SSH_CONFIG_FILE)
        starts_proxy = kwargs.get("ssh_proxy_enabled", True) and not kwargs.get("ssh_proxy")
        self._proxy_command = (
            lookup_ssh_config(ssh_address_or_host, config_file).get("proxycommand")
            if starts_proxy
            else None
        )
        # Rejects an unknown host before sshtunnel loads agent and identity keys for it.
        resolved = resolve_ssh_config(ssh_address_or_host, ssh_port, config_file)
        self._find_known_keys(*resolved)
        super().__init__(ssh_address_or_host, ssh_port=ssh_port, **kwargs)
        # sshtunnel's own resolution decides where it connects, so look up that address too if
        # it differs.
        if (self.ssh_host, self.ssh_port) != resolved:
            self._find_known_keys(self.ssh_host, self.ssh_port)

    def _find_known_keys(self, host: str, port: int) -> None:
        self._known_hosts_entry = known_hosts_name(host, port)
        self._host_keys = self._known_host_keys(self._known_hosts_entry)
        # A matching @revoked line may name the key the host presents, and only the transport sees
        # that key, so it decides the error then.
        if not (self._host_keys.known or self._host_keys.revoked or self._accept_unknown):
            raise paramiko.SSHException(
                f"Host key verification failed: {self._known_hosts_entry} is not in"
                f" known_hosts. {TRUST_HOST_HINT}"
            )

    @classmethod
    def _read_ssh_config(
        cls,
        ssh_host,
        ssh_config_file,
        ssh_username=None,
        ssh_pkey=None,
        ssh_port=None,
        ssh_proxy=None,
        compression=None,
        logger=None,
    ):
        host, username, pkey, port, _, compression = super()._read_ssh_config(
            ssh_host,
            ssh_config_file,
            ssh_username,
            ssh_pkey,
            ssh_port,
            ssh_proxy or _NO_PROXY,
            compression,
            logger,
        )
        return host, username, pkey, port, ssh_proxy, compression

    def _get_transport(self):
        if self._proxy_command:
            # sshtunnel opens a transport for each credential it tries and closes the ones that
            # fail, which ends their proxy, so each transport gets a new ProxyCommand.
            self.ssh_proxy = paramiko.ProxyCommand(self._proxy_command)
        try:
            transport = super()._get_transport()
        except Exception:
            if self._proxy_command:
                self.ssh_proxy.close()
            raise
        # sshtunnel builds a plain Transport, with its proxy and socket settings, and then calls
        # connect() on it; this adds the host key check to that handshake.
        transport.__class__ = KnownHostsTransport
        transport.check_against(self._known_hosts_entry, self._host_keys, self._accept_unknown)
        return transport
