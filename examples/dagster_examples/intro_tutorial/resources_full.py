from dagster import (
    resource,
    Dict,
    execute_pipeline,
    Field,
    ModeDefinition,
    PipelineDefinition,
    RunConfig,
    String,
    solid,
)

from dagster_slack import slack_resource


@solid(required_resources={'say_hi'})
def a_solid(context):
    context.resources.say_hi.chat.post_message(channel='#dagster', text='Hello from Dagster!')


class FileSaver:
    def __init__(self, output):
        self.output = output

        class Chat:
            @classmethod
            def post_message(cls, channel, text):
                with open(self.output, 'a') as f:
                    f.write('%s -- %s\n' % (channel, text))

        self.chat = Chat


@resource(Field(Dict({'output': Field(String)})))
def save_to_file_resource(context):
    return FileSaver(context.resource_config['output'])


def define_resources_pipeline():
    return PipelineDefinition(
        name='resources_pipeline',
        solids=[a_solid],
        mode_definitions=[
            ModeDefinition(name='production', resources={'say_hi': slack_resource}),
            ModeDefinition(name='local', resources={'say_hi': save_to_file_resource}),
        ],
    )


if __name__ == '__main__':
    execute_pipeline(
        define_resources_pipeline(),
        run_config=RunConfig(mode='production'),
        environment_dict={
            'resources': {'say_hi': {'config': {'token': 'xoxp-1234123412341234-12341234-1234'}}}
        },
    )

    execute_pipeline(
        define_resources_pipeline(),
        run_config=RunConfig(mode='local'),
        environment_dict={'resources': {'say_hi': {'config': {'output': '/tmp/dagster-messages'}}}},
    )
