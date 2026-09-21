# To learn more about Dagster resources, see https://docs.dagster.io/api/dagster/resources

from dagster_slack import SlackResource

import dagster as dg


@dg.asset
def slack_message(slack: SlackResource):
    slack.get_client().chat_postMessage(channel="#noise", text=":wave: hey there!")


defs = dg.Definitions(
    assets=[slack_message],
    resources={"slack": SlackResource(token=dg.EnvVar("SLACK_TOKEN"))},
)
