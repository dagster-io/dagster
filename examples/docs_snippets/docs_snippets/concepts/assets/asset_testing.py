from dagster import AssetExecutionContext, asset, build_asset_context

# start_simple_asset


@asset
def my_simple_asset():
    return [1, 2, 3]


# end_simple_asset

# start_test_simple_asset


def test_my_simple_asset():
    result = my_simple_asset()
    assert result == [1, 2, 3]


# end_test_simple_asset

# start_more_complex_asset


@asset
def more_complex_asset(my_simple_asset):
    return my_simple_asset + [4, 5, 6]


# end_more_complex_asset

# start_test_more_complex_asset


def test_more_complex_asset():
    result = more_complex_asset([0])
    assert result == [0, 4, 5, 6]


# end_test_more_complex_asset

# start_with_context_asset


@asset
def uses_context(context: AssetExecutionContext):
    context.log.info(context.run.run_id)
    return "bar"


# end_with_context_asset

# start_test_with_context_asset


def test_uses_context():
    context = build_asset_context()
    result = uses_context(context)
    assert result == "bar"


# end_test_with_context_asset


from typing import Any, Dict

import requests

from dagster import Config, ConfigurableResource

# start_asset_with_resource


class MyConfig(Config):
    api_url: str


class MyAPIResource(ConfigurableResource):
    def query(self, url) -> dict[str, Any]:
        return requests.get(url).json()


@asset
def uses_config_and_resource(config: MyConfig, my_api: MyAPIResource):
    return my_api.query(config.api_url)


def test_uses_resource() -> None:
    result = uses_config_and_resource(
        config=MyConfig(api_url="https://dagster.io"), my_api=MyAPIResource()
    )
    assert result == {"foo": "bar"}


# end_asset_with_resource
