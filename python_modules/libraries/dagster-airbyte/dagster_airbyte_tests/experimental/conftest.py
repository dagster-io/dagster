from typing import Iterator

import pytest
import responses
from dagster_airbyte.resources import AIRBYTE_API_BASE, AIRBYTE_API_VERSION

# Taken from Airbyte API documentation
# https://reference.airbyte.com/reference/createaccesstoken
SAMPLE_ACCESS_TOKEN = {"access_token": "some_access_token"}


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
