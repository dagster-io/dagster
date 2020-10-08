from slackclient import SlackClient

from dagster import Field, StringSource, resource, seven


class SlackConnection:
    def __init__(self, token):
        self.token = token
        self.sc = SlackClient(self.token)

        class _Chat:
            @classmethod
            def post_message(
                cls,
                channel="#noise",
                username="dagsterbot",
                text="Hello from Dagster!",
                # pylint: disable=line-too-long
                icon_url="https://user-images.githubusercontent.com/609349/57993619-9ff2ee00-7a6e-11e9-9184-b3414e3eeb30.png",
                attachments=None,
            ):
                """slack_resource.chat.post_message() : chat.postMessage

                See https://api.slack.com/methods/chat.postMessage
                """
                api_params = {
                    "channel": channel,
                    "username": username,
                    "text": text,
                    "icon_url": icon_url,
                    "attachments": seven.json.dumps(attachments),
                }
                return self.sc.api_call("chat.postMessage", **api_params)

        self.chat = _Chat

    def api_call(self, method, timeout=None, **kwargs):
        return self.sc.api_call(method, timeout, **kwargs)


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

    By configuring this Slack resource, you can post messages to Slack from any Dagster solid:

    Examples:

    .. code-block:: python

        import os

        from dagster import solid, execute_pipeline, ModeDefinition
        from dagster_slack import slack_resource


        @solid(required_resource_keys={'slack'})
        def slack_solid(context):
            context.resources.slack.chat.post_message(channel='#noise', text=':wave: hey there!')

        @pipeline(
            mode_defs=[ModeDefinition(resource_defs={'slack': slack_resource})],
        )
        def slack_pipeline():
            slack_solid()

        execute_pipeline(
            slack_pipeline, {'resources': {'slack': {'config': {'token': os.getenv('SLACK_TOKEN')}}}}
        )

    """
    return SlackConnection(context.resource_config.get("token"))
