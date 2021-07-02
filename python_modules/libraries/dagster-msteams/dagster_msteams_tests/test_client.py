import json

from mock import patch


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_post_message(mock_teams_post_message, json_message, teams_client):

    body = {"ok": True}
    mock_teams_post_message.return_value = {
        "status": 200,
        "body": json.dumps(body),
        "headers": "",
    }
    teams_client.post_message(json_message)
    assert mock_teams_post_message.called
