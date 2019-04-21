from slackclient import SlackClient

from dagster import seven
from dagster import Dict, Field, ResourceDefinition, String


class SlackConnection:
    def __init__(self, token):
        self.token = token
        self.sc = SlackClient(self.token)

    def post(
        self,
        channel='#noise',
        username='dagsterbot',
        text='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        # pylint: disable=line-too-long
        icon_url='https://user-images.githubusercontent.com/609349/56463858-9d2eab80-6391-11e9-8288-e606fdf674b5.png',
        attachments=None,
    ):
        method = 'chat.postMessage'
        api_params = {
            'channel': channel,
            'username': username,
            'text': text,
            'icon_url': icon_url,
            'attachments': seven.json.dumps(attachments),
        }
        self.sc.api_call(method, **api_params)


def define_slack_resource():
    return ResourceDefinition(
        resource_fn=lambda init_context: SlackConnection(init_context.resource_config['token']),
        config_field=Field(Dict({'token': Field(String)})),
        description='''This resource is for posting messages to Slack''',
    )
