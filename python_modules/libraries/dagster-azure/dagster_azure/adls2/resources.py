from dagster_azure.blob.utils import create_blob_client

from dagster import Field, Selector, StringSource, resource

from .utils import create_adls2_client


@resource(
    {
        'storage_account': Field(StringSource, description='The storage account name.'),
        'credential': Field(
            Selector(
                {
                    'sas': Field(StringSource, description='SAS token for the account.'),
                    'key': Field(StringSource, description='Shared Access Key for the account'),
                }
            ),
            description='The credentials with which to authenticate.',
        ),
    }
)
def adls2_resource(context):
    '''Resource that gives solids access to Azure Data Lake Storage Gen2.

    The underlying client is a :py:class:`~azure.storage.filedatalake.DataLakeServiceClient`.

    Attach this resource definition to a :py:class:`~dagster.ModeDefinition` in order to make it
    available to your solids.

    Example:

        .. code-block:: python

            from dagster import ModeDefinition, execute_solid, solid
            from dagster_azure.adls2 import adls2_resource

            @solid(required_resource_keys={'adls2'})
            def example_adls2_solid(context):
                return list(context.resources.adls2.list_file_systems())

            result = execute_solid(
                example_adls2_solid,
                run_config={
                    'resources': {
                        'adls2': {
                            'config': {
                                'storage_account': 'my_storage_account'
                            }
                        }
                    }
                },
                mode_def=ModeDefinition(resource_defs={'adls2': adls2_resource}),
            )

    Note that your solids must also declare that they require this resource with
    `required_resource_keys`, or it will not be initialized for the execution of their compute
    functions.

    You may pass credentials to this resource using either a SAS token or a key, using
    environment variables if desired:

    .. code-block:: YAML

        resources:
          adls2:
            config:
              storage_account: my_storage_account
              # str: The storage account name.
              credential:
                sas: my_sas_token
                # str: the SAS token for the account.
                key:
                  env: AZURE_DATA_LAKE_STORAGE_KEY
                # str: The shared access key for the account.
    '''
    storage_account = context.resource_config['storage_account']
    credential = context.resource_config["credential"].copy().popitem()[1]
    return ADLS2Resource(storage_account, credential)


class ADLS2Resource(object):
    '''Resource containing clients to access Azure Data Lake Storage Gen2.

    Contains a client for both the Data Lake and Blob APIs, to work around the limitations
    of each.
    '''

    def __init__(self, storage_account, credential):
        self._adls2_client = create_adls2_client(storage_account, credential)
        self._blob_client = create_blob_client(storage_account, credential)

    @property
    def adls2_client(self):
        return self._adls2_client

    @property
    def blob_client(self):
        return self._blob_client
