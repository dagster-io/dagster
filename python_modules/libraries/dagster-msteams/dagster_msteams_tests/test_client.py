from typing import Any

import pytest
from dagster_msteams.client import Link, TeamsClient

from dagster_msteams_tests.conftest import LEGACY_WEBHOOK_URL, WEBHOOK_URL


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
