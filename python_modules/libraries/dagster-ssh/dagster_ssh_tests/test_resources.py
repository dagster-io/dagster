import logging

from dagster.seven import mock

from dagster_ssh.resources import SSHResource


@mock.patch('paramiko.SSHClient')
def test_ssh_connection_with_password(ssh_mock):
    ssh_resource = SSHResource(
        remote_host='remote_host',
        remote_port=12345,
        username='username',
        password='password',
        key_file='fake.file',
        timeout=10,
        keepalive_interval=30,
        compress=True,
        no_host_key_check=False,
        allow_host_key_change=False,
        logger=logging.root.getChild('test_resources'),
    )

    with ssh_resource.get_connection():
        ssh_mock.return_value.connect.assert_called_once_with(
            hostname='remote_host',
            username='username',
            password='password',
            key_filename='fake.file',
            timeout=10,
            compress=True,
            port=12345,
            sock=None,
            look_for_keys=False,
        )


@mock.patch('paramiko.SSHClient')
def test_ssh_connection_without_password(ssh_mock):
    ssh_resource = SSHResource(
        remote_host='remote_host',
        remote_port=12345,
        username='username',
        password=None,
        timeout=10,
        key_file='fake.file',
        keepalive_interval=30,
        compress=True,
        no_host_key_check=False,
        allow_host_key_change=False,
        logger=logging.root.getChild('test_resources'),
    )

    with ssh_resource.get_connection():
        ssh_mock.return_value.connect.assert_called_once_with(
            hostname='remote_host',
            username='username',
            key_filename='fake.file',
            timeout=10,
            compress=True,
            port=12345,
            sock=None,
        )


@mock.patch('dagster_ssh.resources.SSHTunnelForwarder')
def test_tunnel_with_password(ssh_mock):
    ssh_resource = SSHResource(
        remote_host='remote_host',
        remote_port=12345,
        username='username',
        password='password',
        timeout=10,
        key_file='fake.file',
        keepalive_interval=30,
        compress=True,
        no_host_key_check=False,
        allow_host_key_change=False,
        logger=logging.root.getChild('test_resources'),
    )

    with ssh_resource.get_tunnel(1234):
        ssh_mock.assert_called_once_with(
            'remote_host',
            ssh_port=12345,
            ssh_username='username',
            ssh_password='password',
            ssh_pkey='fake.file',
            ssh_proxy=None,
            local_bind_address=('localhost',),
            remote_bind_address=('localhost', 1234),
            logger=ssh_resource.log,
        )


@mock.patch('dagster_ssh.resources.SSHTunnelForwarder')
def test_tunnel_without_password(ssh_mock):
    ssh_resource = SSHResource(
        remote_host='remote_host',
        remote_port=12345,
        username='username',
        password=None,
        timeout=10,
        key_file='fake.file',
        keepalive_interval=30,
        compress=True,
        no_host_key_check=False,
        allow_host_key_change=False,
        logger=logging.root.getChild('test_resources'),
    )

    with ssh_resource.get_tunnel(1234):
        ssh_mock.assert_called_once_with(
            'remote_host',
            ssh_port=12345,
            ssh_username='username',
            ssh_pkey='fake.file',
            ssh_proxy=None,
            local_bind_address=('localhost',),
            remote_bind_address=('localhost', 1234),
            host_pkey_directories=[],
            logger=ssh_resource.log,
        )
