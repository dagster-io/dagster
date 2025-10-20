# start_asset_marker

from azure.ai.ml import command
from dagster_azure.pipes import (
    PipesAzureBlobStorageContextInjector,
    PipesAzureBlobStorageMessageReader,
    PipesAzureMLClient,
)

import dagster as dg


@dg.asset
def azureml_training_job(
    context: dg.AssetExecutionContext,
    pipes_azureml: PipesAzureMLClient,
):
    return pipes_azureml.run(
        context=context,
        command=command(
            code="./src",  # Path to your source code
            command="python train.py",
            environment="dagster-env:1",
            compute="my-compute-cluster",
            display_name="ml-training-job",
        ),
    ).get_results()

# end_asset_marker


# start_definitions_marker
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

import dagster as dg


@dg.definitions
def resources() -> dg.Definitions:
    azure_blob_storage = BlobServiceClient(
        account_url="https://<DAGSTER-STORAGE-ACCOUNT>.blob.core.windows.net/",
        credential=DefaultAzureCredential()
    )
    azure_ml = MLClient(
        credential=DefaultAzureCredential(),
        subscription_id="<SUBSCRIPTION-ID>",
        resource_group_name="<RESOURCE-GROUP-NAME>",
        workspace_name="<WORKSPACE-NAME>",
    )

    return dg.Definitions(
        resources={
            "pipes_azureml": PipesAzureMLClient(
                client=azure_ml,
                context_injector=PipesAzureBlobStorageContextInjector(
                    container="dagster", 
                    client=azure_blob_storage
                ),
                message_reader=PipesAzureBlobStorageMessageReader(
                    container="dagster", 
                    client=azure_blob_storage
                )
            ),
        },
    )

# end_definitions_marker