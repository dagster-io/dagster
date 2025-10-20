from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from dagster_pipes import (
    PipesAzureBlobStorageContextLoader,
    PipesAzureBlobStorageMessageWriter,
    PipesContext,
    open_dagster_pipes,
)

AZURE_STORAGE_ACCOUNT = "<AZURE-STORAGE-ACCOUNT>"

# Initialize Azure Blob Storage client
blob_client = BlobServiceClient(
    account_url=f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=DefaultAzureCredential()
)

# Set up Pipes communication via Azure Blob Storage
context_loader = PipesAzureBlobStorageContextLoader(client=blob_client)
message_writer = PipesAzureBlobStorageMessageWriter(client=blob_client)

with open_dagster_pipes(
    context_loader=context_loader,
    message_writer=message_writer
) as context:
    # Access Dagster context
    context.log.info("Running Azure ML job")
    
    # Your ML Training code here
    # ...
    # ...
    # ...
    result = {"accuracy": "0.83"}

    # Report materialization back to Dagster
    context.report_asset_materialization(
        metadata={
            "accuracy": {"raw_value": result["accuracy"], "type": "float"}
        }
    )

