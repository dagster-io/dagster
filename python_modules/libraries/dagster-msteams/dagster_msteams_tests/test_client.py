from typing import Any

from dagster_msteams.adaptive_card import AdaptiveCard
from dagster_msteams.card import Card
from dagster_msteams.client import TeamsClient
from dagster_msteams.utils import MSTeamsHyperlink, build_message_with_link

from dagster_msteams_tests.conftest import LEGACY_WEBHOOK_URL, WEBHOOK_URL


def test_client_compatible_with_legacy_webhook(mock_post_method, snapshot: Any):
    teams_client = TeamsClient(hook_url=LEGACY_WEBHOOK_URL)

    card = Card()
    card.add_attachment(
        build_message_with_link(
            is_legacy_webhook=True,
            text="Run failed!",
            link=MSTeamsHyperlink(text="View in Dagit", url="http://localhost:3000"),
        )
    )
    teams_client.post_message(card.payload)

    snapshot.assert_match(mock_post_method.call_args_list)


def test_client_compatible_with_workflow_webhook(mock_post_method, snapshot: Any):
    teams_client = TeamsClient(hook_url=WEBHOOK_URL)

    card = AdaptiveCard()
    card.add_attachment(
        build_message_with_link(
            is_legacy_webhook=False,
            text="Run failed!",
            link=MSTeamsHyperlink(text="View in Dagit", url="http://localhost:3000"),
        )
    )
    teams_client.post_message(card.payload)

    snapshot.assert_match(mock_post_method.call_args_list)
