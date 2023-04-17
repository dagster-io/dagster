import mock

from docs_snippets.concepts.assets.asset_config import (
    MyAssetConfig as MyConfigurableAssetConfig,
)
from docs_snippets.concepts.assets.asset_config import my_configurable_asset


def test_my_configurable_asset() -> None:
    with mock.patch("requests.get") as mock_get:
        mock_get.return_value = mock.Mock()
        mock_get.return_value.json.return_value = {"foo": "bar"}

        assert (
            my_configurable_asset(MyConfigurableAssetConfig(api_endpoint="bar"))
        ) == {"foo": "bar"}

        assert mock_get.call_args[0][0] == "bar/data"

        assert (
            my_configurable_asset(config=MyConfigurableAssetConfig(api_endpoint="bar"))
        ) == {"foo": "bar"}
