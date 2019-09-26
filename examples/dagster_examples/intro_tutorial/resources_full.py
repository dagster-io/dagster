from dagster_slack import slack_resource

from dagster import (
    Field,
    ModeDefinition,
    RunConfig,
    String,
    execute_pipeline,
    pipeline,
    resource,
    solid,
)

HELLO_MESSAGE = '"Hello, World" from Dagster!'


@solid(required_resource_keys={'slack'})
def post_hello_message(context):
    context.resources.slack.chat.post_message(channel='#dagster', text=HELLO_MESSAGE)


class SlackToFile:
    def __init__(self, output_path):
        self.chat = ChatToFile(output_path)


class ChatToFile:
    def __init__(self, output_path):
        self.output_path = output_path

    def post_message(self, channel, text):
        with open(self.output_path, 'a') as f:
            f.write('%s -- %s\n' % (channel, text))


@resource({'output_path': Field(String)})
def slack_to_file_resource(context):
    return SlackToFile(context.resource_config['output_path'])


@pipeline(
    mode_defs=[
        ModeDefinition(name='production', resource_defs={'slack': slack_resource}),
        ModeDefinition(name='local', resource_defs={'slack': slack_to_file_resource}),
    ]
)
def resources_pipeline():
    post_hello_message()


if __name__ == '__main__':
    execute_pipeline(
        resources_pipeline,
        run_config=RunConfig(mode='production'),
        environment_dict={
            'resources': {'slack': {'config': {'token': 'xoxp-1234123412341234-12341234-1234'}}}
        },
    )

    execute_pipeline(
        resources_pipeline,
        run_config=RunConfig(mode='local'),
        environment_dict={
            'resources': {'slack': {'config': {'output_path': '/tmp/dagster-messages'}}}
        },
    )
