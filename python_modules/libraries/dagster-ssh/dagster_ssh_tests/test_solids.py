import os

from dagster_ssh import sftp_solid, ssh_resource

from dagster import ModeDefinition, execute_solid
from dagster.seven import get_system_temp_directory


def test_sftp_solid(sftpserver):
    tmp_path = get_system_temp_directory()
    readme_file = os.path.join(tmp_path, 'readme.txt')

    with sftpserver.serve_content({'a_dir': {'readme.txt': 'hello, world'}}):
        result = execute_solid(
            sftp_solid,
            ModeDefinition(resource_defs={'ssh_resource': ssh_resource}),
            environment_dict={
                'solids': {
                    'sftp_solid': {
                        'config': {
                            'local_filepath': readme_file,
                            'remote_filepath': 'a_dir/readme.txt',
                            'operation': 'GET',
                        }
                    }
                },
                'resources': {
                    'ssh_resource': {
                        'config': {
                            'remote_host': sftpserver.host,
                            'remote_port': sftpserver.port,
                            'username': 'user',
                            'password': 'pw',
                            'no_host_key_check': True,
                        }
                    }
                },
            },
        )
        assert result.success

    with open(readme_file, 'rb') as f:
        contents = f.read()
        assert b'hello, world' in contents
