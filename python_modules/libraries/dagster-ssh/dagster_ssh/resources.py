import contextlib
import getpass
import logging
import os
from io import StringIO

import paramiko
from dagster import (
    BoolSource,
    Field as DagsterField,
    IntSource,
    StringSource,
    _check as check,
    get_dagster_logger,
    resource,
)
from dagster._annotations import beta
from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.execution.context.init import InitResourceContext
from dagster._utils import mkdir_p
from paramiko.client import SSHClient
from paramiko.config import SSH_PORT
from pydantic import Field, PrivateAttr
from sshtunnel import SSHTunnelForwarder

from dagster_ssh.host_keys import (
    AcceptCheckedHostKeyPolicy,
    KnownHostTunnelForwarder,
    client_transport_factory,
    known_hosts_name,
)
from dagster_ssh.known_hosts import KnownHostKeys, known_keys
from dagster_ssh.ssh_config import lookup_ssh_config

SYSTEM_KNOWN_HOSTS_FILE = "/etc/ssh/ssh_known_hosts"


def key_from_str(key_str):
    """Creates a paramiko SSH key from a string.

    Args:
        key_str (str): A string containing the private key data.

    Returns:
        paramiko.RSAKey: An RSA key object created from the provided string.

    Raises:
        ValueError: If the key string is invalid or cannot be parsed.
    """
    check.str_param(key_str, "key_str")

    # py2 StringIO doesn't support with
    key_file = StringIO(key_str)
    result = paramiko.RSAKey.from_private_key(key_file)
    key_file.close()
    return result


@beta
class SSHResource(ConfigurableResource):
    """A Dagster resource for establishing SSH connections and performing remote file operations.

    This resource leverages the Paramiko library to provide robust SSH connectivity,
    including support for key-based and password authentication, tunneling, and SFTP transfers.

    Args:
        remote_host (str): The hostname or IP address of the remote server to connect to.
        remote_port (Optional[int]): The SSH port on the remote host. Defaults to standard SSH port 22.
        username (Optional[str]): The username for SSH authentication. If not provided, defaults to the current system user.
        password (Optional[str]): The password for SSH authentication. Not recommended for production use; prefer key-based authentication.
        key_file (Optional[str]): Path to the SSH private key file for authentication.
        key_string (Optional[str]): SSH private key as a string for authentication.
        timeout (int, optional): Connection timeout in seconds. Defaults to 10.
        keepalive_interval (int, optional): Interval for sending SSH keepalive packets. (Defaults to 30 seconds.)
        compress (bool, optional): Whether to compress the SSH transport stream. Defaults to True.
        known_hosts_file (Optional[str]): Path to an extra known_hosts file to trust, in addition to
            ``~/.ssh/known_hosts`` and ``/etc/ssh/ssh_known_hosts``.
        no_host_key_check (bool, optional): Accept a host that has no known_hosts entry, and skip
            known_hosts files that cannot be read. A key that differs from the host's entry, or
            that is marked ``@revoked``, is still rejected. Unsafe: a machine on the network can
            impersonate a host that is not in known_hosts. Defaults to False.
        allow_host_key_change (bool, optional): Ignored. A host whose key differs from its
            known_hosts entry is always rejected, with or without ``no_host_key_check``.

    By default, ``get_connection``, ``get_tunnel``, ``sftp_get``, and ``sftp_put`` verify the host
    key against ``/etc/ssh/ssh_known_hosts``, ``~/.ssh/known_hosts``, and ``known_hosts_file``, and
    reject a host that is not listed there.

    Example:
        Creating an SSH resource with key-based authentication:

        .. code-block:: python

            ssh_resource = SSHResource(
                remote_host="example.com",
                username="myuser", key_file="/path/to/private/key"
            )

        Trusting a host whose key is in a known_hosts file you provide:

        .. code-block:: python

            ssh_resource = SSHResource(
                remote_host="example.com",
                username="myuser",
                key_file="/path/to/private/key",
                known_hosts_file="/path/to/known_hosts",
            )

        Creating an SSH resource with password authentication:

        .. code-block:: python

            ssh_resource = SSHResource(
                remote_host="example.com",
                username="myuser",
                password="my_secure_password"
            )

        Using the resource to transfer a file:

        .. code-block:: python

            local_file = ssh_resource.sftp_get("/remote/path/file.txt", "/local/path/file.txt")
    """

    remote_host: str = Field(description="Remote host to connect to")
    remote_port: int | None = Field(default=None, description="Port of remote host to connect")
    username: str | None = Field(default=None, description="Username to connect to remote host")
    password: str | None = Field(
        default=None, description="Password of the username to connect to remote host"
    )
    key_file: str | None = Field(
        default=None, description="Key file to use to connect to remote host"
    )
    key_string: str | None = Field(
        default=None, description="Key string to use to connect to remote host"
    )
    timeout: int = Field(
        default=10, description="Timeout for the attempt to connect to remote host"
    )
    keepalive_interval: int = Field(
        default=30,
        description="Send a keepalive packet to remote host every keepalive_interval seconds",
    )
    compress: bool = Field(default=True, description="Compress the transport stream")
    known_hosts_file: str | None = Field(
        default=None,
        description=(
            "Extra known_hosts file to trust, in addition to ~/.ssh/known_hosts and"
            " /etc/ssh/ssh_known_hosts"
        ),
    )
    no_host_key_check: bool = Field(
        default=False,
        description=(
            "If True, accept a host that has no known_hosts entry and skip known_hosts files that"
            " cannot be read. A changed or @revoked key is still rejected. Unsafe: a machine on"
            " the network can impersonate a host that is not in known_hosts"
        ),
    )
    allow_host_key_change: bool = Field(
        default=False,
        description=(
            "Ignored. A host whose key differs from its known_hosts entry is always rejected,"
            " with or without no_host_key_check"
        ),
    )

    _logger: logging.Logger | None = PrivateAttr(default=None)

    def set_logger(self, logger: logging.Logger) -> None:
        self._logger = logger

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._logger = context.log

    def _proxy(self) -> paramiko.ProxyCommand | None:
        # A ProxyCommand runs its command when created, so each connection needs its own. Tunnels
        # start their own, per transport.
        proxy_command = lookup_ssh_config(self.remote_host).get("proxycommand")
        return paramiko.ProxyCommand(proxy_command) if proxy_command else None

    def _parsed_key_string(self) -> paramiko.RSAKey | None:
        return key_from_str(self.key_string) if self.key_string is not None else None

    def _resolved_username(self) -> str:
        # Passed explicitly because sshtunnel would prefer the ssh config's User and paramiko
        # would not, so tunnels and connections could log in as different users.
        return self.username or getpass.getuser()

    def _uses_password(self) -> bool:
        return bool(self.password and self.password.strip())

    def _resolved_key_file(self) -> str | None:
        """``key_file``, or the host's ssh config IdentityFile when no other credential is set."""
        if self.key_file or self._uses_password() or self.key_string:
            return self.key_file
        identity_files = lookup_ssh_config(self.remote_host).get("identityfile")
        return identity_files[0] if identity_files else None

    @property
    def log(self) -> logging.Logger:
        return self._logger or get_dagster_logger()

    def _known_host_keys(self, known_hosts_entry: str) -> KnownHostKeys:
        """The keys known_hosts lists for the host.

        A missing ``known_hosts_file`` is an error unless ``no_host_key_check`` is set, which skips
        any file that cannot be read.
        """
        candidates = [
            (SYSTEM_KNOWN_HOSTS_FILE, False),
            (os.path.expanduser("~/.ssh/known_hosts"), False),
        ]
        if self.known_hosts_file:
            candidates.append((os.path.expanduser(self.known_hosts_file), True))
        return known_keys(
            [path for path, required in candidates if self._reads_known_hosts(path, required)],
            known_hosts_entry,
        )

    def _reads_known_hosts(self, path: str, required: bool) -> bool:
        if self.no_host_key_check:
            return os.path.isfile(path) and os.access(path, os.R_OK)
        return required or os.path.isfile(path)

    def _warn_about_host_key_options(self) -> None:
        if self.allow_host_key_change:
            self.log.warning(
                "allow_host_key_change is ignored: a host whose key differs from its known_hosts"
                " entry is always rejected"
            )
        if self.no_host_key_check:
            self.log.warning(
                "no_host_key_check=True accepts a host that is not in known_hosts. This won't"
                " protect that host against Man-In-The-Middle attacks"
            )

    def get_connection(self) -> SSHClient:
        """Opens a SSH connection to the remote host.

        :rtype: paramiko.client.SSHClient
        """
        self._warn_about_host_key_options()
        known_hosts_entry = known_hosts_name(self.remote_host, self.remote_port or SSH_PORT)
        # The transport checks the host key against known_hosts, because paramiko's own loader
        # rejects marker lines and keeps only one key per type.
        transport_factory = client_transport_factory(
            known_hosts_entry, self._known_host_keys(known_hosts_entry), self.no_host_key_check
        )
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(AcceptCheckedHostKeyPolicy())

        key_file = self._resolved_key_file()
        pkey = self._parsed_key_string()
        proxy = self._proxy()
        try:
            if self._uses_password():
                client.connect(
                    hostname=self.remote_host,
                    username=self._resolved_username(),
                    password=self.password,
                    key_filename=key_file,
                    pkey=pkey,
                    timeout=self.timeout,
                    compress=self.compress,
                    port=self.remote_port,  # type: ignore
                    sock=proxy,
                    look_for_keys=False,
                    transport_factory=transport_factory,
                )
            else:
                client.connect(
                    hostname=self.remote_host,
                    username=self._resolved_username(),
                    key_filename=key_file,
                    pkey=pkey,
                    timeout=self.timeout,
                    compress=self.compress,
                    port=self.remote_port,  # type: ignore
                    sock=proxy,
                    transport_factory=transport_factory,
                )
        except BaseException:
            # The proxy may be closed already, through its transport, and closing it again can
            # fail, so a cleanup error must not replace the connect error.
            with contextlib.suppress(OSError):
                client.close()
            if proxy is not None:
                with contextlib.suppress(OSError):
                    proxy.close()
            raise

        if self.keepalive_interval:
            client.get_transport().set_keepalive(self.keepalive_interval)  # type: ignore

        return client

    def get_tunnel(
        self, remote_port, remote_host="localhost", local_port=None
    ) -> SSHTunnelForwarder:
        """Returns an unstarted tunnel to ``remote_host:remote_port`` through the SSH host.

        Unless ``no_host_key_check`` is set, this raises if the SSH host is not in known_hosts.
        The tunnel's ``start()`` raises ``HostKeyRejectedError`` before authenticating if the host
        presents a key that differs from its known_hosts entry or is marked ``@revoked``.
        """
        check.int_param(remote_port, "remote_port")
        check.str_param(remote_host, "remote_host")
        check.opt_int_param(local_port, "local_port")

        if local_port is not None:
            local_bind_address = ("localhost", local_port)
        else:
            local_bind_address = ("localhost",)

        # Will prefer key string if specified, otherwise use the key file
        key_file = self._resolved_key_file()
        key_obj = self._parsed_key_string()
        if key_obj and key_file:
            self.log.warning(
                "SSHResource: key_string and key_file both specified as config. Using key_string."
            )
        pkey = key_obj if key_obj else key_file

        self._warn_about_host_key_options()

        if self._uses_password():
            client = KnownHostTunnelForwarder(
                self.remote_host,
                ssh_port=self.remote_port,
                ssh_username=self._resolved_username(),
                ssh_password=self.password,
                ssh_pkey=pkey,
                local_bind_address=local_bind_address,
                remote_bind_address=(remote_host, remote_port),
                logger=self._logger,
                known_host_keys=self._known_host_keys,
                accept_unknown=self.no_host_key_check,
            )
        else:
            client = KnownHostTunnelForwarder(
                self.remote_host,
                ssh_port=self.remote_port,
                ssh_username=self._resolved_username(),
                ssh_pkey=pkey,
                local_bind_address=local_bind_address,
                remote_bind_address=(remote_host, remote_port),
                host_pkey_directories=[],
                logger=self._logger,
                known_host_keys=self._known_host_keys,
                accept_unknown=self.no_host_key_check,
            )

        return client

    def sftp_get(self, remote_filepath, local_filepath):
        check.str_param(remote_filepath, "remote_filepath")
        check.str_param(local_filepath, "local_filepath")
        conn = self.get_connection()
        with conn.open_sftp() as sftp_client:
            local_folder = os.path.dirname(local_filepath)

            # Create intermediate directories if they don't exist
            mkdir_p(local_folder)

            self.log.info(f"Starting to transfer from {remote_filepath} to {local_filepath}")

            sftp_client.get(remote_filepath, local_filepath)

        conn.close()
        return local_filepath

    def sftp_put(self, remote_filepath, local_filepath, confirm=True):
        check.str_param(remote_filepath, "remote_filepath")
        check.str_param(local_filepath, "local_filepath")
        conn = self.get_connection()
        with conn.open_sftp() as sftp_client:
            self.log.info(f"Starting to transfer file from {local_filepath} to {remote_filepath}")

            sftp_client.put(local_filepath, remote_filepath, confirm=confirm)

        conn.close()
        return local_filepath


@beta
@dagster_maintained_resource
@resource(
    config_schema={
        "remote_host": DagsterField(
            StringSource, description="remote host to connect to", is_required=True
        ),
        "remote_port": DagsterField(
            IntSource,
            description="port of remote host to connect (Default is paramiko SSH_PORT)",
            is_required=False,
            default_value=SSH_PORT,
        ),
        "username": DagsterField(
            StringSource, description="username to connect to the remote_host", is_required=False
        ),
        "password": DagsterField(
            StringSource,
            description="password of the username to connect to the remote_host",
            is_required=False,
        ),
        "key_file": DagsterField(
            StringSource,
            description="key file to use to connect to the remote_host.",
            is_required=False,
        ),
        "key_string": DagsterField(
            StringSource,
            description="key string to use to connect to remote_host",
            is_required=False,
        ),
        "timeout": DagsterField(
            IntSource,
            description="timeout for the attempt to connect to the remote_host.",
            is_required=False,
            default_value=10,
        ),
        "keepalive_interval": DagsterField(
            IntSource,
            description="send a keepalive packet to remote host every keepalive_interval seconds",
            is_required=False,
            default_value=30,
        ),
        "compress": DagsterField(BoolSource, is_required=False, default_value=True),
        "known_hosts_file": DagsterField(
            StringSource,
            description=(
                "extra known_hosts file to trust, in addition to ~/.ssh/known_hosts and"
                " /etc/ssh/ssh_known_hosts"
            ),
            is_required=False,
        ),
        "no_host_key_check": DagsterField(
            BoolSource,
            description=(
                "if True, accept a host that has no known_hosts entry and skip known_hosts files"
                " that cannot be read. A changed or @revoked key is still rejected. Unsafe: a"
                " machine on the network can impersonate a host that is not in known_hosts"
            ),
            is_required=False,
            default_value=False,
        ),
        "allow_host_key_change": DagsterField(
            BoolSource,
            description=(
                "[Deprecated] Ignored. A host whose key differs from its known_hosts entry is"
                " always rejected, with or without no_host_key_check"
            ),
            is_required=False,
            default_value=False,
        ),
    }
)
def ssh_resource(init_context):
    """A Dagster resource factory for creating SSHResource instances.

    This function converts Dagster resource context configuration into an SSHResource
    that can be used for remote SSH connections and file operations.

    Args:
        init_context (InitResourceContext): The Dagster resource initialization context containing configuration parameters.

    Returns:
        SSHResource: A configured SSH resource ready for use in Dagster pipelines.

    Example:
        Configuring the SSH resource in a Dagster pipeline:

        .. code-block:: python

            from dagster import Definitions, job, op
            from dagster_ssh import ssh_resource

            @op
            def transfer_files(ssh):
                ssh.sftp_get("/remote/file", "/local/file")

            @job
            def my_ssh_job():
                transfer_files(ssh=ssh_resource.configured({
                    "remote_host": "example.com",
                    "username": "myuser",
                    "key_file": "/path/to/private/key"
                }))

            Definitions(jobs=[my_ssh_job])
    """
    return SSHResource.from_resource_context(init_context)
