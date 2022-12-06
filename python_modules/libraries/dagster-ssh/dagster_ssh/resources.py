import getpass
import os
from io import StringIO

import paramiko
from dagster import (
    BoolSource,
    Field,
    IntSource,
    StringSource,
    _check as check,
    resource,
)
from dagster._utils import mkdir_p
from dagster._utils.merger import merge_dicts
from paramiko.config import SSH_PORT
from sshtunnel import SSHTunnelForwarder


def key_from_str(key_str):
    """Creates a paramiko SSH key from a string."""
    check.str_param(key_str, "key_str")

    # py2 StringIO doesn't support with
    key_file = StringIO(key_str)
    result = paramiko.RSAKey.from_private_key(key_file)
    key_file.close()
    return result


class SSHResource:
    """
    Resource for ssh remote execution using Paramiko.

    ref: https://github.com/paramiko/paramiko
    """

    def __init__(
        self,
        remote_host,
        remote_port,
        username=None,
        password=None,
        key_file=None,
        key_string=None,
        timeout=10,
        keepalive_interval=30,
        compress=True,
        no_host_key_check=True,
        allow_host_key_change=False,
        logger=None,
    ):
        self.remote_host = check.str_param(remote_host, "remote_host")
        self.remote_port = check.opt_int_param(remote_port, "remote_port")
        self.username = check.opt_str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.key_file = check.opt_str_param(key_file, "key_file")
        self.timeout = check.opt_int_param(timeout, "timeout")
        self.keepalive_interval = check.opt_int_param(keepalive_interval, "keepalive_interval")
        self.compress = check.opt_bool_param(compress, "compress")
        self.no_host_key_check = check.opt_bool_param(no_host_key_check, "no_host_key_check")
        self.allow_host_key_change = check.opt_bool_param(
            allow_host_key_change, "allow_host_key_change"
        )
        self.log = logger

        self.host_proxy = None

        # Create RSAKey object from private key string
        self.key_obj = key_from_str(key_string) if key_string is not None else None

        # Auto detecting username values from system
        if not self.username:
            logger.debug(
                "username to ssh to host: %s is not specified. Using system's default provided by"
                " getpass.getuser()"
                % self.remote_host
            )
            self.username = getpass.getuser()

        user_ssh_config_filename = os.path.expanduser("~/.ssh/config")
        if os.path.isfile(user_ssh_config_filename):
            ssh_conf = paramiko.SSHConfig()
            ssh_conf.parse(open(user_ssh_config_filename, encoding="utf8"))
            host_info = ssh_conf.lookup(self.remote_host)
            if host_info and host_info.get("proxycommand"):
                self.host_proxy = paramiko.ProxyCommand(host_info.get("proxycommand"))

            if not (self.password or self.key_file):
                if host_info and host_info.get("identityfile"):
                    self.key_file = host_info.get("identityfile")[0]

    def get_connection(self):
        """
        Opens a SSH connection to the remote host.

        :rtype: paramiko.client.SSHClient
        """
        client = paramiko.SSHClient()
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
                pkey=self.key_obj,
                timeout=self.timeout,
                compress=self.compress,
                port=self.remote_port,
                sock=self.host_proxy,
                look_for_keys=False,
            )
        else:
            client.connect(
                hostname=self.remote_host,
                username=self.username,
                key_filename=self.key_file,
                pkey=self.key_obj,
                timeout=self.timeout,
                compress=self.compress,
                port=self.remote_port,
                sock=self.host_proxy,
            )

        if self.keepalive_interval:
            client.get_transport().set_keepalive(self.keepalive_interval)

        return client

    def get_tunnel(self, remote_port, remote_host="localhost", local_port=None):
        check.int_param(remote_port, "remote_port")
        check.str_param(remote_host, "remote_host")
        check.opt_int_param(local_port, "local_port")

        if local_port is not None:
            local_bind_address = ("localhost", local_port)
        else:
            local_bind_address = ("localhost",)

        # Will prefer key string if specified, otherwise use the key file
        pkey = self.key_obj if self.key_obj else self.key_file

        if self.password and self.password.strip():
            client = SSHTunnelForwarder(
                self.remote_host,
                ssh_port=self.remote_port,
                ssh_username=self.username,
                ssh_password=self.password,
                ssh_pkey=pkey,
                ssh_proxy=self.host_proxy,
                local_bind_address=local_bind_address,
                remote_bind_address=(remote_host, remote_port),
                logger=self.log,
            )
        else:
            client = SSHTunnelForwarder(
                self.remote_host,
                ssh_port=self.remote_port,
                ssh_username=self.username,
                ssh_pkey=pkey,
                ssh_proxy=self.host_proxy,
                local_bind_address=local_bind_address,
                remote_bind_address=(remote_host, remote_port),
                host_pkey_directories=[],
                logger=self.log,
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

            self.log.info(
                "Starting to transfer from {0} to {1}".format(remote_filepath, local_filepath)
            )

            sftp_client.get(remote_filepath, local_filepath)

        conn.close()
        return local_filepath

    def sftp_put(self, remote_filepath, local_filepath, confirm=True):
        check.str_param(remote_filepath, "remote_filepath")
        check.str_param(local_filepath, "local_filepath")
        conn = self.get_connection()
        with conn.open_sftp() as sftp_client:
            self.log.info(
                "Starting to transfer file from {0} to {1}".format(local_filepath, remote_filepath)
            )

            sftp_client.put(local_filepath, remote_filepath, confirm=confirm)

        conn.close()
        return local_filepath


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
        "allow_host_key_change": Field(BoolSource, is_required=False, default_value=False),
    }
)
def ssh_resource(init_context):
    args = init_context.resource_config
    args = merge_dicts(init_context.resource_config, {"logger": init_context.log})
    return SSHResource(**args)
