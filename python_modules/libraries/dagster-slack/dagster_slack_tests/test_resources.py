import responses
from dagster_slack import slack_resource

from dagster import ModeDefinition, execute_solid, solid


@responses.activate
def test_slack_resource():
    @solid(required_resource_keys={'slack'})
    def slack_solid(context):
        assert context.resources.slack
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                'https://slack.com/api/chat.postMessage',
                status=200,
                json={
                    'ok': True,
                    'channel': 'SOME_CHANNEL',
                    'ts': '1555993892.000300',
                    'headers': {'Content-Type': 'application/json; charset=utf-8'},
                },
            )
            context.resources.slack.chat.post_message()

    result = execute_solid(
        slack_solid,
        environment_dict={
            'resources': {'slack': {'config': {'token': 'xoxp-1234123412341234-12341234-1234'}}}
        },
        mode_def=ModeDefinition(resource_defs={'slack': slack_resource}),
    )
    assert result.success
