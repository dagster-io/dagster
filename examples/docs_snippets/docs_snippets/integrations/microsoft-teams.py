# Read the docs on Resources to learn more: https://docs.dagster.io/deployment/resources
from dagster_msteams import Card, MSTeamsResource

import dagster as dg


@dg.asset
def microsoft_teams_message(msteams: MSTeamsResource):
    card = Card()
    card.add_attachment(text_message="Hello there!")
    msteams.get_client().post_message(payload=card.payload)


defs = dg.Definitions(
    assets=[microsoft_teams_message],
    resources={"msteams": MSTeamsResource(hook_url=dg.EnvVar("TEAMS_WEBHOOK_URL"))},
)
