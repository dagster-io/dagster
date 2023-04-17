import requests

# start_example
from dagster import Config, asset


class MyAssetConfig(Config):
    api_endpoint: str


@asset
def my_configurable_asset(config: MyAssetConfig):
    data = requests.get(f"{config.api_endpoint}/data").json()
    return data


# end_example
