import requests

# start_example
from dagster import Config, asset


@asset
def my_upstream_asset() -> int:
    return 5


class MyDownstreamAssetConfig(Config):
    api_endpoint: str


@asset
def my_downstream_asset(config: MyDownstreamAssetConfig, my_upstream_asset: int) -> int:
    data = requests.get(f"{config.api_endpoint}/data").json()
    return data["value"] + my_upstream_asset


# end_example
