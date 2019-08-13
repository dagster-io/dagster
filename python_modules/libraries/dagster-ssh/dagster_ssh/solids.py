import os

import six

from dagster import DagsterExecutionStepExecutionError, Enum, EnumValue, Field, solid
from dagster.utils import mkdir_p


@solid(
    config={
        'remote_host': Field(
            str,
            is_optional=True,
            description='Nullable. If provided, it will replace the `remote_host` which was defined'
            ' in `ssh_resource`.',
        ),
        'local_filepath': Field(
            str, is_optional=False, description='local file path to get or put.'
        ),
        'remote_filepath': Field(
            str, is_optional=False, description='remote file path to get or put.'
        ),
        'operation': Field(
            Enum('SFTPOperation', [EnumValue('GET'), EnumValue('PUT')]),
            is_optional=True,
            default_value='PUT',
            description='specify operation \'GET\' or \'PUT\', defaults to PUT',
        ),
        'confirm': Field(
            bool,
            is_optional=True,
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

    remote_host = context.solid_config.get('remote_host')
    local_filepath = context.solid_config.get('local_filepath')
    remote_filepath = context.solid_config.get('remote_filepath')
    operation = context.solid_config.get('operation')
    confirm = context.solid_config.get('confirm')

    file_msg = None
    try:
        if remote_host is not None:
            context.log.info(
                'remote_host is provided explicitly. '
                + 'It will replace the remote_host which was defined '
                + 'in ssh_resource or predefined in connection of ssh_conn_id.'
            )
            context.resources.ssh_resource.remote_host = remote_host

        with context.resources.ssh_resource.get_connection() as ssh_client:
            sftp_client = ssh_client.open_sftp()
            if operation == 'GET':
                local_folder = os.path.dirname(local_filepath)

                # Create intermediate directories if they don't exist
                mkdir_p(local_folder)

                file_msg = 'from {0} to {1}'.format(remote_filepath, local_filepath)

                context.log.info('Starting to transfer %s' % file_msg)

                sftp_client.get(remote_filepath, local_filepath)
            else:
                file_msg = 'from {0} to {1}'.format(local_filepath, remote_filepath)

                context.log.info('Starting to transfer file %s' % file_msg)

                sftp_client.put(local_filepath, remote_filepath, confirm=confirm)

    except Exception as err:  # pylint: disable=broad-except
        six.raise_from(
            DagsterExecutionStepExecutionError('Error while transferring {0}'.format(file_msg)), err
        )

    return local_filepath
