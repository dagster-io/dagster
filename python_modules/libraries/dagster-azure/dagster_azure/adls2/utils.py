from azure.storage.filedatalake import DataLakeServiceClient


def _create_url(storage_account, subdomain):
    return "https://{}.{}.core.windows.net/".format(storage_account, subdomain)


def create_adls2_client(storage_account, credential):
    """
    Create an ADLS2 client.
    """
    account_url = _create_url(storage_account, "dfs")
    return DataLakeServiceClient(account_url, credential)
