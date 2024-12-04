from typing import Iterator

import pytest
import responses
from dagster_airbyte.resources import AIRBYTE_API_BASE, AIRBYTE_API_VERSION

TEST_WORKSPACE_ID = "some_workspace_id"
TEST_CLIENT_ID = "some_client_id"
TEST_CLIENT_SECRET = "some_client_secret"

TEST_ACCESS_TOKEN = "some_access_token"

# Taken from Airbyte API documentation
# https://reference.airbyte.com/reference/createaccesstoken
SAMPLE_ACCESS_TOKEN = {"access_token": TEST_ACCESS_TOKEN}


@pytest.fixture(
    name="base_api_mocks",
)
def base_api_mocks_fixture() -> Iterator[responses.RequestsMock]:
    with responses.RequestsMock() as response:
        response.add(
            method=responses.POST,
            url=f"{AIRBYTE_API_BASE}/{AIRBYTE_API_VERSION}/applications/token",
            json=SAMPLE_ACCESS_TOKEN,
            status=201,
        )
        yield response
