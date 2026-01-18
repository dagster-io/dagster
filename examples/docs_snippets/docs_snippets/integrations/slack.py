# Read the docs on Resources to learn more: https://docs.dagster.io/deployment/resources

from dagster_slack import SlackResource

import dagster as dg


@dg.asset
def slack_message(slack: SlackResource):
    slack.get_client().chat_postMessage(channel="#noise", text=":wave: hey there!")


defs = dg.Definitions(
    assets=[slack_message],
    resources={"slack": SlackResource(token=dg.EnvVar("SLACK_TOKEN"))},
)
