import requests

# start_example
from dagster import Config, asset


class MyDownstreamAssetConfig(Config):
    api_endpoint: str


@asset
def my_downstream_asset(config: MyDownstreamAssetConfig):
    data = requests.get(f"{config.api_endpoint}/data").json()
    ...


# end_example
