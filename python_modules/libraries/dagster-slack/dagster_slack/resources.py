from dagster import Field, StringSource, resource
from slack_sdk.web.client import WebClient


@resource(
    {
        "token": Field(
            StringSource,
            description="""To configure access to the Slack API, you'll need an access
                    token provisioned with access to your Slack workspace.

                    Tokens are typically either user tokens or bot tokens. For programmatic posting
                    to Slack from this resource, you probably want to provision and use a bot token.

                    More in the Slack API documentation here: https://api.slack.com/docs/token-types
                    """,
        )
    },
    description="This resource is for connecting to Slack",
)
def slack_resource(context):
    """This resource is for connecting to Slack.

    The resource object is a `slack_sdk.WebClient`.

    By configuring this Slack resource, you can post messages to Slack from any Dagster op:

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
    return WebClient(context.resource_config.get("token"))
