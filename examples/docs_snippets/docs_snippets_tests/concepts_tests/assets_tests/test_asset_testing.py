from unittest import mock


def test_uses_resource() -> None:
    from docs_snippets.concepts.assets.asset_testing import test_uses_resource

    with mock.patch("requests.get") as mock_get:
        mock_get.return_value = mock.Mock()
        mock_get.return_value.json.return_value = {"foo": "bar"}

        test_uses_resource()
        assert mock_get.call_args[0][0] == "https://dagster.io"
