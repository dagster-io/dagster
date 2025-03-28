import dagster as dg


# Warning! This is not the right way to create assets
@dg.asset
def download_files():
    # Download files from S3, the web, etc.
    ...


@dg.asset
def unzip_files():
    # Unzip files to local disk or persistent storage
    ...


@dg.asset
def load_data():
    # Read data previously written and store in a data warehouse
    ...
