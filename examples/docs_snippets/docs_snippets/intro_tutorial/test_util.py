from functools import update_wrapper
from pathlib import Path
from unittest.mock import MagicMock, patch


def patch_cereal_requests(fn):
    with open(Path(__file__).parent / "cereal.csv", encoding="utf8") as f:
        cereal_text = f.read()

    @patch("requests.get")
    def with_patch(mock_requests_get):
        mock_requests_get.return_value = MagicMock(text=cereal_text)
        return fn()

    update_wrapper(with_patch, fn)

    return with_patch
