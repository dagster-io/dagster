import getpass
import logging
import os
from io import StringIO
from typing import Optional

import paramiko
from dagster import (
    BoolSource,
    Field,
    IntSource,
    StringSource,
    _check as check,
    resource,
)
from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.execution.context.init import InitResourceContext
from dagster._utils import mkdir_p
from paramiko.client import SSHClient
from paramiko.config import SSH_PORT
from pydantic import (
    Field as PyField,
    PrivateAttr,
)
from sshtunnel import SSHTunnelForwarder


def key_from_str(key_str):
    """Creates a paramiko SSH key from a string."""
    check.str_param(key_str, "key_str")

    # py2 StringIO doesn't support with
    key_file = StringIO(key_str)
    result = paramiko.RSAKey.from_private_key(key_file)
    key_file.close()
    return result


class SSHResource(ConfigurableResource):
    """Resource for ssh remote execution using Paramiko.

    ref: https://github.com/paramiko/paramiko
    """

    remote_host: str = PyField(description="Remote host to connect to")
    remote_port: Optional[int] = PyField(default=None, description="Port of remote host to connect")
    username: Optional[str] = PyField(
        default=None, description="Username to connect to remote host"
    )
    password: Optional[str] = PyField(
        default=None, description="Password of the username to connect to remote host"
    )
    key_file: Optional[str] = PyField(
        default=None, description="Key file to use to connect to remote host"
    )
    key_string: Optional[str] = PyField(
        default=None, description="Key string to use to connect to remote host"
    )
    timeout: int = PyField(
        default=10, description="Timeout for the attempt to connect to remote host"
    )
    keepalive_interval: int = PyField(
        default=30,
        description="Send a keepalive packet to remote host every keepalive_interval seconds",
    )
    compress: bool = PyField(default=True, description="Compress the transport stream")
    no_host_key_check: bool = PyField(
        default=True,
        description=(
            "If True, the host key will not be verified. This is unsafe and not recommended"
        ),
    )
    allow_host_key_change: bool = PyField(
        default=False,
        description="If True, allow connecting to hosts whose host key has changed",
    )

    _logger: Optional[logging.Logger] = PrivateAttr(default=None)
    _host_proxy: Optional[paramiko.ProxyCommand] = PrivateAttr(default=None)
    _key_obj: Optional[paramiko.RSAKey] = PrivateAttr(default=None)

    def set_logger(self, logger: logging.Logger) ->None:
        self._logger = logger

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._logger = context.log
        self._host_proxy = None

        # Create RSAKey object from private key string
        self._key_obj = key_from_str(self.key_string) if self.key_string is not None else None

        # Auto detecting username values from system
        if not self.username:
            if self._logger:
                self._logger.debug(
                    "username to ssh to host: %s is not specified. Using system's default provided"
                    " by getpass.getuser()"
                    % self.remote_host
                )
            self.username = getpass.getuser()

        user_ssh_config_filename = os.path.expanduser("~/.ssh/config")
        if os.path.isfile(user_ssh_config_filename):
            ssh_conf = paramiko.SSHConfig()
            ssh_conf.parse(open(user_ssh_config_filename, encoding="utf8"))
            host_info = ssh_conf.lookup(self.remote_host)

            proxy_command = host_info.get("proxycommand")
            if host_info and proxy_command:
                self._host_proxy = paramiko.ProxyCommand(proxy_command)

            if not (self.password or self.key_file):
                identify_file = host_info.get("identityfile")
                if host_info and identify_file:
                    self.key_file = identify_file[0]

    @property
    def log(self):
        return self._logger

    def get_connection(self) -> SSHClient:
        """Opens a SSH connection to the remote host.

        :rtype: paramiko.client.SSHClient
        """
        client = paramiko.SSHClient()
        client.load_system_host_keys()

        if not self.allow_host_key_change:
            self.log.warning(
                "Remote Identification Change is not verified. This won't protect against "
                "Man-In-The-Middle attacks"
            )
            client.load_system_host_keys()
        if self.no_host_key_check:
            self.log.warning(
                "No Host Key Verification. This won't protect against Man-In-The-Middle attacks"
            )
            # Default is RejectPolicy
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.password and self.password.strip():
            client.connect(
                hostname=self.remote_host,
                username=self.username,
                password=self.password,
                key_filename=self.key_file,
                pkey=self._key_obj,
                timeout=self.timeout,
                compress=self.compress,
                port=self.remote_port,  # type: ignore
                sock=self._host_proxy,  # type: ignore
                look_for_keys=False,
            )
        else:
            client.connect(
                hostname=self.remote_host,
                username=self.username,
                key_filename=self.key_file,
                pkey=self._key_obj,
                timeout=self.timeout,
                compress=self.compress,
                port=self.remote_port,  # type: ignore
                sock=self._host_proxy,  # type: ignore
            )

        if self.keepalive_interval:
            client.get_transport().set_keepalive(self.keepalive_interval)  # type: ignore

        return client

    def get_tunnel(
        self, remote_port, remote_host="localhost", local_port=None
    ) -> SSHTunnelForwarder:
        check.int_param(remote_port, "remote_port")
        check.str_param(remote_host, "remote_host")
        check.opt_int_param(local_port, "local_port")

        if local_port is not None:
            local_bind_address = ("localhost", local_port)
        else:
            local_bind_address = ("localhost",)

        # Will prefer key string if specified, otherwise use the key file
        pkey = self._key_obj if self._key_obj else self.key_file

        if self.password and self.password.strip():
            client = SSHTunnelForwarder(
                self.remote_host,
                ssh_port=self.remote_port,
                ssh_username=self.username,
                ssh_password=self.password,
                ssh_pkey=pkey,
                ssh_proxy=self._host_proxy,
                local_bind_address=local_bind_address,
                remote_bind_address=(remote_host, remote_port),
                logger=self._logger,  # type: ignore
            )
        else:
            client = SSHTunnelForwarder(
                self.remote_host,
                ssh_port=self.remote_port,
                ssh_username=self.username,
                ssh_pkey=pkey,
                ssh_proxy=self._host_proxy,
                local_bind_address=local_bind_address,
                remote_bind_address=(remote_host, remote_port),
                host_pkey_directories=[],
                logger=self._logger,  # type: ignore
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


@dagster_maintained_resource
@resource(
    config_schema={
        "remote_host": Field(
            StringSource, description="remote host to connect to", is_required=True
        ),
        "remote_port": Field(
            IntSource,
            description="port of remote host to connect (Default is paramiko SSH_PORT)",
            is_required=False,
            default_value=SSH_PORT,
        ),
        "username": Field(
            StringSource, description="username to connect to the remote_host", is_required=False
        ),
        "password": Field(
            StringSource,
            description="password of the username to connect to the remote_host",
            is_required=False,
        ),
        "key_file": Field(
            StringSource,
            description="key file to use to connect to the remote_host.",
            is_required=False,
        ),
        "key_string": Field(
            StringSource,
            description="key string to use to connect to remote_host",
            is_required=False,
        ),
        "timeout": Field(
            IntSource,
            description="timeout for the attempt to connect to the remote_host.",
            is_required=False,
            default_value=10,
        ),
        "keepalive_interval": Field(
            IntSource,
            description="send a keepalive packet to remote host every keepalive_interval seconds",
            is_required=False,
            default_value=30,
        ),
        "compress": Field(BoolSource, is_required=False, default_value=True),
        "no_host_key_check": Field(BoolSource, is_required=False, default_value=True),
        "allow_host_key_change": Field(
            BoolSource, description="[Deprecated]", is_required=False, default_value=False
        ),
    }
)
def ssh_resource(init_context):
    return SSHResource.from_resource_context(init_context)
