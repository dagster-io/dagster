import os

from dagster import Enum, EnumValue, Field, solid
from dagster.utils import mkdir_p


@solid(
    config={
        'local_filepath': Field(
            str, is_required=True, description='local file path to get or put.'
        ),
        'remote_filepath': Field(
            str, is_required=True, description='remote file path to get or put.'
        ),
        'operation': Field(
            Enum('SFTPOperation', [EnumValue('GET'), EnumValue('PUT')]),
            is_required=False,
            default_value='PUT',
            description='specify operation \'GET\' or \'PUT\', defaults to PUT',
        ),
        'confirm': Field(
            bool,
            is_required=False,
            default_value=True,
            description='specify if the SFTP operation should be confirmed, defaults to True',
        ),
    },
    required_resource_keys={'ssh_resource'},
)
def sftp_solid(context):
    '''
    Ported from Airflow's SFTPOperator.

    sftp_solid: for transferring files from remote host to local or vice a versa. This solid uses
    ssh_resource to open a SFTP transport channel that serve as basis for file transfer.
    '''
    local_filepath = context.solid_config.get('local_filepath')
    remote_filepath = context.solid_config.get('remote_filepath')
    operation = context.solid_config.get('operation')
    confirm = context.solid_config.get('confirm')

    with context.resources.ssh_resource.get_connection() as ssh_client:
        sftp_client = ssh_client.open_sftp()
        if operation == 'GET':
            local_folder = os.path.dirname(local_filepath)

            # Create intermediate directories if they don't exist
            mkdir_p(local_folder)

            context.log.info(
                'Starting to transfer from {0} to {1}'.format(remote_filepath, local_filepath)
            )
            sftp_client.get(remote_filepath, local_filepath)

        else:
            context.log.info(
                'Starting to transfer file from {0} to {1}'.format(local_filepath, remote_filepath)
            )

            sftp_client.put(local_filepath, remote_filepath, confirm=confirm)

    return local_filepath
