from unittest.mock import MagicMock, mock_open, patch

from dagster import load_assets_from_modules, materialize_to_memory
from docs_snippets.tutorial.managing_your_own_io import assets as assets_to_test


@patch("urllib.request.urlretrieve")
@patch("zipfile.ZipFile")
@patch("csv.reader")
def test_stopword_assets(mock_urlretrieve, mock_zipfile, mock_csv):
    mock_csv.return_value = [["hello"]]

    mock = MagicMock()
    mock_open(mock)

    with patch("builtins.open", mock, create=True) as patched:
        assets = load_assets_from_modules([assets_to_test])
        assert materialize_to_memory(assets)
