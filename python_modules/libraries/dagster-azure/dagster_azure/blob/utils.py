from azure.storage.blob import BlobServiceClient


def _create_url(storage_account, subdomain):
    return "https://{}.{}.core.windows.net/".format(storage_account, subdomain)


def create_blob_client(storage_account, credential):
    """
    Create a Blob Storage client.
    """
    account_url = _create_url(storage_account, "blob")
    if hasattr(credential, "account_key"):
        credential = credential.account_key
    return BlobServiceClient(account_url, credential)
