from unittest.mock import patch

import pytest
from dagster_msteams.client import TeamsClient


@pytest.fixture
def json_message():
    test_json_message = {
        "type": "text",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.hero",
                "content": {
                    "title": "Dagster Pipeline Alert",
                    "subtitle": "Hello there !",
                },
            }
        ],
    }
    return test_json_message


@pytest.fixture
def teams_client():
    client = TeamsClient(hook_url="https://some_url_here/")
    return client


@pytest.fixture(scope="function", name="mock_post_method")
def create_mock_post_method():
    with patch("dagster_msteams.client.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Success"}
        mock_response.text = "1"
        yield mock_post


LEGACY_WEBHOOK_URL = "https://foo.webhook.office.com/bar/baz"
WEBHOOK_URL = "https://foo.westus.logic.azure.com:443/workflows/8be36cde7f394925af220480f6701bd0"
