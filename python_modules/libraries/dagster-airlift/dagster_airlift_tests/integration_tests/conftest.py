from pathlib import Path
from typing import Any

import pytest
import requests


def assert_link_exists(link_name: str, link_url: Any):
    assert isinstance(link_url, str)
    assert requests.get(link_url).status_code == 200, f"{link_name} is broken"


@pytest.fixture(name="dags_dir")
def default_dags_dir():
    return Path(__file__).parent / "dags"
