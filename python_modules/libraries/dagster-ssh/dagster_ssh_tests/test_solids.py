import os

from dagster import ModeDefinition, execute_solid
from dagster.seven import get_system_temp_directory

from dagster_ssh import sftp_solid, ssh_resource


def test_sftp_solid():
    tmp_path = get_system_temp_directory()
    readme_file = os.path.join(tmp_path, 'readme.txt')

    result = execute_solid(
        sftp_solid,
        ModeDefinition(resource_defs={'ssh_resource': ssh_resource}),
        environment_dict={
            'solids': {
                'sftp_solid': {
                    'config': {
                        'local_filepath': readme_file,
                        'remote_filepath': 'readme.txt',
                        'operation': 'GET',
                    }
                }
            },
            'resources': {
                'ssh_resource': {
                    'config': {
                        # Per https://www.sftp.net/public-online-sftp-servers
                        'remote_host': 'test.rebex.net',
                        'remote_port': 22,
                        'username': 'demo',
                        'password': 'password',
                        'no_host_key_check': True,
                    }
                }
            },
        },
    )
    assert result.success

    with open(readme_file, 'rb') as f:
        contents = f.read()
        assert b'you are connected to an FTP or SFTP server' in contents
