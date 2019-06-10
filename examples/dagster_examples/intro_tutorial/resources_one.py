from dagster import execute_pipeline, ModeDefinition, PipelineDefinition, solid

from dagster_slack import slack_resource


@solid(required_resources={'say_hi'})
def a_solid(context):
    context.resources.say_hi.chat.post_message(channel='#dagster', text='Hello from Dagster!')


def define_resources_pipeline():
    return PipelineDefinition(
        name='resources_pipeline',
        solids=[a_solid],
        mode_definitions=[ModeDefinition(resources={'say_hi': slack_resource})],
    )


if __name__ == '__main__':
    execute_pipeline(
        define_resources_pipeline(),
        environment_dict={
            'resources': {'say_hi': {'config': {'token': 'xoxp-1234123412341234-12341234-1234'}}}
        },
    )
