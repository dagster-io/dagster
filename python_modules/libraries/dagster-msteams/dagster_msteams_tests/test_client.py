import json
from typing import Any
from unittest.mock import patch

import pytest
from dagster_msteams.client import Link, TeamsClient


@pytest.fixture(scope="function", name="mock_post_method")
def create_mock_post_method():
    with patch("dagster_msteams.client.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Success"}
        mock_response.text = "1"
        yield mock_post


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_post_message(mock_teams_post_message, json_message, teams_client):
    body = {"ok": True}
    mock_teams_post_message.return_value = {
        "status": 200,
        "body": json.dumps(body),
        "headers": "",
    }
    teams_client.post_message(json_message)
    assert mock_teams_post_message.called


LEGACY_WEBHOOK_URL = "https://foo.webhook.office.com/bar/baz"
WEBHOOK_URL = "https://foo.westus.logic.azure.com:443/workflows/8be36cde7f394925af220480f6701bd0"


@pytest.mark.parametrize(
    "webhook_url",
    [
        LEGACY_WEBHOOK_URL,
        WEBHOOK_URL,
    ],
)
def test_client_compatible_with_legacy_and_workflow_webhooks(
    webhook_url: str, mock_post_method, snapshot: Any
):
    teams_client = TeamsClient(hook_url=webhook_url)

    teams_client.post_message(
        "Run failed!", link=Link(text="View in Dagit", url="http://localhost:3000")
    )
    snapshot.assert_match(mock_post_method.call_args_list)
