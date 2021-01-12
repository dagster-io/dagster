import logging
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dagster import Field, ModeDefinition, execute_solid, solid
from dagster.seven import get_system_temp_directory, mock
from dagster_ssh.resources import SSHResource, key_from_str
from dagster_ssh.resources import ssh_resource as sshresource


def generate_ssh_key():
    # generate private/public key pair
    key = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, key_size=2048)

    # get private key in PEM container format
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


@mock.patch("paramiko.SSHClient")
def test_ssh_connection_with_password(ssh_mock):
    ssh_resource = SSHResource(
        remote_host="remote_host",
        remote_port=12345,
        username="username",
        password="password",
        key_file="fake.file",
        timeout=10,
        keepalive_interval=30,
        compress=True,
        no_host_key_check=False,
        allow_host_key_change=False,
        logger=logging.root.getChild("test_resources"),
    )

    with ssh_resource.get_connection():
        ssh_mock.return_value.connect.assert_called_once_with(
            hostname="remote_host",
            username="username",
            password="password",
            pkey=None,
            key_filename="fake.file",
            timeout=10,
            compress=True,
            port=12345,
            sock=None,
            look_for_keys=False,
        )


@mock.patch("paramiko.SSHClient")
def test_ssh_connection_without_password(ssh_mock):
    ssh_resource = SSHResource(
        remote_host="remote_host",
        remote_port=12345,
        username="username",
        password=None,
        timeout=10,
        key_file="fake.file",
        keepalive_interval=30,
        compress=True,
        no_host_key_check=False,
        allow_host_key_change=False,
        logger=logging.root.getChild("test_resources"),
    )

    with ssh_resource.get_connection():
        ssh_mock.return_value.connect.assert_called_once_with(
            hostname="remote_host",
            username="username",
            pkey=None,
            key_filename="fake.file",
            timeout=10,
            compress=True,
            port=12345,
            sock=None,
        )


@mock.patch("paramiko.SSHClient")
def test_ssh_connection_with_key_string(ssh_mock):
    ssh_key = generate_ssh_key()

    ssh_resource = SSHResource(
        remote_host="remote_host",
        remote_port=12345,
        username="username",
        password=None,
        timeout=10,
        key_string=ssh_key,
        keepalive_interval=30,
        compress=True,
        no_host_key_check=False,
        allow_host_key_change=False,
        logger=logging.root.getChild("test_resources"),
    )

    with ssh_resource.get_connection():
        ssh_mock.return_value.connect.assert_called_once_with(
            hostname="remote_host",
            username="username",
            key_filename=None,
            pkey=key_from_str(ssh_key),
            timeout=10,
            compress=True,
            port=12345,
            sock=None,
        )


@mock.patch("dagster_ssh.resources.SSHTunnelForwarder")
def test_tunnel_with_password(ssh_mock):
    ssh_resource = SSHResource(
        remote_host="remote_host",
        remote_port=12345,
        username="username",
        password="password",
        timeout=10,
        key_file="fake.file",
        keepalive_interval=30,
        compress=True,
        no_host_key_check=False,
        allow_host_key_change=False,
        logger=logging.root.getChild("test_resources"),
    )

    with ssh_resource.get_tunnel(1234):
        ssh_mock.assert_called_once_with(
            "remote_host",
            ssh_port=12345,
            ssh_username="username",
            ssh_password="password",
            ssh_pkey="fake.file",
            ssh_proxy=None,
            local_bind_address=("localhost",),
            remote_bind_address=("localhost", 1234),
            logger=ssh_resource.log,
        )


@mock.patch("dagster_ssh.resources.SSHTunnelForwarder")
def test_tunnel_without_password(ssh_mock):
    ssh_resource = SSHResource(
        remote_host="remote_host",
        remote_port=12345,
        username="username",
        password=None,
        timeout=10,
        key_file="fake.file",
        keepalive_interval=30,
        compress=True,
        no_host_key_check=False,
        allow_host_key_change=False,
        logger=logging.root.getChild("test_resources"),
    )

    with ssh_resource.get_tunnel(1234):
        ssh_mock.assert_called_once_with(
            "remote_host",
            ssh_port=12345,
            ssh_username="username",
            ssh_pkey="fake.file",
            ssh_proxy=None,
            local_bind_address=("localhost",),
            remote_bind_address=("localhost", 1234),
            host_pkey_directories=[],
            logger=ssh_resource.log,
        )


@mock.patch("dagster_ssh.resources.SSHTunnelForwarder")
def test_tunnel_with_string_key(ssh_mock):
    ssh_key = generate_ssh_key()

    ssh_resource = SSHResource(
        remote_host="remote_host",
        remote_port=12345,
        username="username",
        password=None,
        timeout=10,
        key_string=ssh_key,
        keepalive_interval=30,
        compress=True,
        no_host_key_check=False,
        allow_host_key_change=False,
        logger=logging.root.getChild("test_resources"),
    )

    with ssh_resource.get_tunnel(1234):
        ssh_mock.assert_called_once_with(
            "remote_host",
            ssh_port=12345,
            ssh_username="username",
            ssh_pkey=key_from_str(ssh_key),
            ssh_proxy=None,
            local_bind_address=("localhost",),
            remote_bind_address=("localhost", 1234),
            host_pkey_directories=[],
            logger=ssh_resource.log,
        )


def test_ssh_sftp(sftpserver):
    tmp_path = get_system_temp_directory()
    readme_file = os.path.join(tmp_path, "readme.txt")

    @solid(
        config_schema={
            "local_filepath": Field(str, is_required=True, description="local file path to get"),
            "remote_filepath": Field(str, is_required=True, description="remote file path to get"),
        },
        required_resource_keys={"ssh_resource"},
    )
    def sftp_solid_get(context):
        local_filepath = context.solid_config.get("local_filepath")
        remote_filepath = context.solid_config.get("remote_filepath")
        return context.resources.ssh_resource.sftp_get(remote_filepath, local_filepath)

    with sftpserver.serve_content({"a_dir": {"readme.txt": "hello, world"}}):
        result = execute_solid(
            sftp_solid_get,
            ModeDefinition(resource_defs={"ssh_resource": sshresource}),
            run_config={
                "solids": {
                    "sftp_solid_get": {
                        "config": {
                            "local_filepath": readme_file,
                            "remote_filepath": "a_dir/readme.txt",
                        }
                    }
                },
                "resources": {
                    "ssh_resource": {
                        "config": {
                            "remote_host": sftpserver.host,
                            "remote_port": sftpserver.port,
                            "username": "user",
                            "password": "pw",
                            "no_host_key_check": True,
                        }
                    }
                },
            },
        )
        assert result.success

    with open(readme_file, "rb") as f:
        contents = f.read()
        assert b"hello, world" in contents
