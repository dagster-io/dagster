from dagster import ConfigurableResource, resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from pydantic import Field
from slack_sdk.web.client import WebClient


class SlackResource(ConfigurableResource):
    """This resource is for connecting to Slack.

    By configuring this Slack resource, you can post messages to Slack from any Dagster op, asset, schedule or sensor.

    Examples:
        .. code-block:: python

            import os

            from dagster import EnvVar, job, op
            from dagster_slack import SlackResource


            @op
            def slack_op(slack: SlackResource):
                slack.get_client().chat_postMessage(channel='#noise', text=':wave: hey there!')

            @job
            def slack_job():
                slack_op()

            defs = Definitions(
                jobs=[slack_job],
                resources={
                    "slack": SlackResource(token=EnvVar("MY_SLACK_TOKEN")),
                },
            )
    """

    token: str = Field(
        description=(
            "To configure access to the Slack API, you'll need an access"
            " token provisioned with access to your Slack workspace."
            " Tokens are typically either user tokens or bot tokens. For programmatic posting"
            " to Slack from this resource, you probably want to provision and use a bot token."
            " More in the Slack API documentation here: https://api.slack.com/docs/token-types"
        ),
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> WebClient:
        """Returns a ``slack_sdk.WebClient`` for interacting with the Slack API."""
        return WebClient(self.token)


@dagster_maintained_resource
@resource(
    config_schema=SlackResource.to_config_schema(),
)
def slack_resource(context) -> WebClient:
    """This resource is for connecting to Slack.

    The resource object is a `slack_sdk.WebClient`.

    By configuring this Slack resource, you can post messages to Slack from any Dagster op, asset, schedule or sensor.

    Examples:
        .. code-block:: python

            import os

            from dagster import job, op
            from dagster_slack import slack_resource


            @op(required_resource_keys={'slack'})
            def slack_op(context):
                context.resources.slack.chat_postMessage(channel='#noise', text=':wave: hey there!')

            @job(resource_defs={'slack': slack_resource})
            def slack_job():
                slack_op()

            slack_job.execute_in_process(
                run_config={'resources': {'slack': {'config': {'token': os.getenv('SLACK_TOKEN')}}}}
            )
    """
    return SlackResource.from_resource_context(context).get_client()
