from typing import Any, Union

from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeLeaseClient
from dagster import (
    Config,
    ConfigurableResource,
    Field as DagsterField,
    Permissive,
    Selector,
    StringSource,
    resource,
)
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._utils.cached_method import cached_method
from dagster._utils.merger import merge_dicts
from pydantic import Field
from typing_extensions import Literal

from dagster_azure.adls2.file_manager import ADLS2FileManager
from dagster_azure.adls2.io_manager import InitResourceContext
from dagster_azure.adls2.utils import DataLakeServiceClient, create_adls2_client
from dagster_azure.blob.utils import BlobServiceClient, create_blob_client


class ADLS2SASToken(Config):
    credential_type: Literal["sas"] = "sas"
    token: str


class ADLS2Key(Config):
    credential_type: Literal["key"] = "key"
    key: str


class ADLS2DefaultAzureCredential(Config):
    credential_type: Literal["default_azure_credential"] = "default_azure_credential"
    kwargs: dict[str, Any]


class ADLS2BaseResource(ConfigurableResource):
    storage_account: str = Field(description="The storage account name.")
    credential: Union[ADLS2SASToken, ADLS2Key, ADLS2DefaultAzureCredential] = Field(
        discriminator="credential_type", description="The credentials with which to authenticate."
    )


DEFAULT_AZURE_CREDENTIAL_CONFIG = DagsterField(
    Permissive(
        description="Uses DefaultAzureCredential to authenticate and passed as keyword arguments",
    )
)

ADLS2_CLIENT_CONFIG = {
    "storage_account": DagsterField(StringSource, description="The storage account name."),
    "credential": DagsterField(
        Selector(
            {
                "sas": DagsterField(StringSource, description="SAS token for the account."),
                "key": DagsterField(StringSource, description="Shared Access Key for the account."),
                "DefaultAzureCredential": DEFAULT_AZURE_CREDENTIAL_CONFIG,
            }
        ),
        description="The credentials with which to authenticate.",
    ),
}


class ADLS2Resource(ADLS2BaseResource):
    """Resource containing clients to access Azure Data Lake Storage Gen2.

    Contains a client for both the Data Lake and Blob APIs, to work around the limitations
    of each.

    Example usage:

    Attach this resource to your Definitions to be used by assets and jobs.

    .. code-block:: python

        from dagster import Definitions, asset, job, op
        from dagster_azure.adls2 import ADLS2Resource, ADLS2SASToken

        @asset
        def asset1(adls2: ADLS2Resource):
            adls2.adls2_client.list_file_systems()
            ...

        @op
        def my_op(adls2: ADLS2Resource):
            adls2.adls2_client.list_file_systems()
            ...

        @job
        def my_job():
            my_op()

        defs = Definitions(
            assets=[asset1],
            jobs=[my_job],
            resources={
                "adls2": ADLS2Resource(
                    storage_account="my-storage-account",
                    credential=ADLS2SASToken(token="my-sas-token"),
                )
            },
        )


    Attach this resource to your job to make it available to your ops.

    .. code-block:: python

        from dagster import job, op
        from dagster_azure.adls2 import ADLS2Resource, ADLS2SASToken

        @op
        def my_op(adls2: ADLS2Resource):
            adls2.adls2_client.list_file_systems()
            ...

        @job(
            resource_defs={
                "adls2": ADLS2Resource(
                    storage_account="my-storage-account",
                    credential=ADLS2SASToken(token="my-sas-token"),
                )
            },
        )
        def my_job():
            my_op()
    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @property
    @cached_method
    def _raw_credential(self) -> Any:
        if isinstance(self.credential, ADLS2Key):
            return self.credential.key
        elif isinstance(self.credential, ADLS2SASToken):
            return self.credential.token
        else:
            return DefaultAzureCredential(**self.credential.kwargs)

    @property
    @cached_method
    def adls2_client(self) -> DataLakeServiceClient:
        return create_adls2_client(self.storage_account, self._raw_credential)

    @property
    @cached_method
    def blob_client(self) -> BlobServiceClient:
        return create_blob_client(self.storage_account, self._raw_credential)

    @property
    def lease_client_constructor(self) -> Any:
        return DataLakeLeaseClient


# Due to a limitation of the discriminated union type, we can't directly mirror these old
# config fields in the new resource config. Instead, we'll just use the old config fields
# to construct the new config and then use that to construct the resource.
@dagster_maintained_resource
@resource(ADLS2_CLIENT_CONFIG)
def adls2_resource(context: InitResourceContext) -> ADLS2Resource:
    """Resource that gives ops access to Azure Data Lake Storage Gen2.

    The underlying client is a :py:class:`~azure.storage.filedatalake.DataLakeServiceClient`.

    Attach this resource definition to a :py:class:`~dagster.JobDefinition` in order to make it
    available to your ops.

    Example:
        .. code-block:: python

            from dagster import job, op
            from dagster_azure.adls2 import adls2_resource

            @op(required_resource_keys={'adls2'})
            def example_adls2_op(context):
                return list(context.resources.adls2.adls2_client.list_file_systems())

            @job(resource_defs={"adls2": adls2_resource})
            def my_job():
                example_adls2_op()

    Note that your ops must also declare that they require this resource with
    `required_resource_keys`, or it will not be initialized for the execution of their compute
    functions.

    You may pass credentials to this resource using either a SAS token, a key or by passing the
    `DefaultAzureCredential` object.

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
                DefaultAzureCredential: {}
                # dict: The keyword arguments used for DefaultAzureCredential
                # or leave the object empty for no arguments
                DefaultAzureCredential:
                    exclude_environment_credential: true

    """
    return _adls2_resource_from_config(context.resource_config)


@dagster_maintained_resource
@resource(
    merge_dicts(
        ADLS2_CLIENT_CONFIG,
        {
            "adls2_file_system": DagsterField(
                StringSource, description="ADLS Gen2 file system name"
            ),
            "adls2_prefix": DagsterField(StringSource, is_required=False, default_value="dagster"),
        },
    )
)
def adls2_file_manager(context: InitResourceContext) -> ADLS2FileManager:
    """FileManager that provides abstract access to ADLS2.

    Implements the :py:class:`~dagster._core.storage.file_manager.FileManager` API.
    """
    adls2_client = _adls2_resource_from_config(context.resource_config).adls2_client

    return ADLS2FileManager(
        adls2_client=adls2_client,
        file_system=context.resource_config["adls2_file_system"],
        prefix=context.resource_config["adls2_prefix"],
    )


def _adls2_resource_from_config(config) -> ADLS2Resource:
    """Args:
        config: A configuration containing the fields in ADLS2_CLIENT_CONFIG.

    Returns: An adls2 client.
    """
    storage_account = config["storage_account"]
    if "DefaultAzureCredential" in config["credential"]:
        credential = ADLS2DefaultAzureCredential(
            kwargs=config["credential"]["DefaultAzureCredential"]
        )
    elif "sas" in config["credential"]:
        credential = ADLS2SASToken(token=config["credential"]["sas"])
    else:
        credential = ADLS2Key(key=config["credential"]["key"])

    return ADLS2Resource(storage_account=storage_account, credential=credential)
