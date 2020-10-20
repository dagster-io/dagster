import json

from dagster import ModeDefinition, execute_solid, solid
from dagster_slack import slack_resource
from mock import patch


@patch("slack.web.base_client.BaseClient._perform_urllib_http_request")
def test_slack_resource(mock_urllib_http_request):
    @solid(required_resource_keys={"slack"})
    def slack_solid(context):
        assert context.resources.slack
        body = {"ok": True}
        mock_urllib_http_request.return_value = {
            "status": 200,
            "body": json.dumps(body),
            "headers": "",
        }

        context.resources.slack.chat_postMessage(channel="#random", text=":wave: hey there!")

        assert mock_urllib_http_request.called

    result = execute_solid(
        slack_solid,
        run_config={
            "resources": {"slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}}
        },
        mode_def=ModeDefinition(resource_defs={"slack": slack_resource}),
    )
    assert result.success
