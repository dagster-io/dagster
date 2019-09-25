from dagster_slack import slack_resource

from dagster import ModeDefinition, execute_pipeline, pipeline, solid


@solid(required_resource_keys={'slack'})
def post_hello_message(context):
    context.resources.slack.chat.post_message(
        channel='#dagster', text='"Hello, World" from Dagster!'
    )


@pipeline(mode_defs=[ModeDefinition(resource_defs={'slack': slack_resource})])
def resources_pipeline():
    post_hello_message()


if __name__ == '__main__':
    execute_pipeline(
        resources_pipeline,
        environment_dict={
            'resources': {'slack': {'config': {'token': 'xoxp-1234123412341234-12341234-1234'}}}
        },
    )
