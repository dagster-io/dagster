import json
import sys

import pytest
import responses
from dagster_slack import slack_resource
from mock import patch

from dagster import ModeDefinition, execute_solid, solid


@pytest.mark.skipif(sys.version_info < (3, 5), reason="Test for slackclient 2.x")
@patch("slack.web.base_client.BaseClient._perform_urllib_http_request")
def test_slack_resource_version2(mock_urllib_http_request):
    @solid(required_resource_keys={"slack"})
    def slack_solid(context):
        assert context.resources.slack
        body = {"ok": True}
        mock_urllib_http_request.return_value = {
            "status": 200,
            "body": json.dumps(body),
            "headers": "",
        }

        context.resources.slack.chat.post_message(channel="#random", text=":wave: hey there!")

        assert mock_urllib_http_request.called

    result = execute_solid(
        slack_solid,
        run_config={
            "resources": {"slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}}
        },
        mode_def=ModeDefinition(resource_defs={"slack": slack_resource}),
    )
    assert result.success


@pytest.mark.skipif(sys.version_info.major >= 3, reason="Test for slackclient 1.x")
@responses.activate
def test_slack_resource_version1():
    @solid(required_resource_keys={"slack"})
    def slack_solid(context):
        assert context.resources.slack
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                "https://slack.com/api/chat.postMessage",
                status=200,
                json={
                    "ok": True,
                    "channel": "SOME_CHANNEL",
                    "ts": "1555993892.000300",
                    "headers": {"Content-Type": "application/json; charset=utf-8"},
                },
            )
            context.resources.slack.chat.post_message(channel="#random", text=":wave: hey there!")

    result = execute_solid(
        slack_solid,
        run_config={
            "resources": {"slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}}
        },
        mode_def=ModeDefinition(resource_defs={"slack": slack_resource}),
    )
    assert result.success
