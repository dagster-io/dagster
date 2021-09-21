import pytest
from dagster_msteams.client import TeamsClient


@pytest.fixture
def json_message():
    test_json_message = {
        "type": "text",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.hero",
                "content": {
                    "title": "Dagster Pipeline Alert",
                    "subtitle": "Hello there !",
                },
            }
        ],
    }
    return test_json_message


@pytest.fixture
def teams_client():
    client = TeamsClient(hook_url="https://some_url_here/")
    return client
