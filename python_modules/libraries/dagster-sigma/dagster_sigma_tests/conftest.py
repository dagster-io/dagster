import uuid

import pytest
import responses
from dagster_sigma import SigmaBaseUrl


@pytest.fixture(name="sigma_auth_token")
def sigma_auth_fixture() -> str:
    fake_access_token: str = uuid.uuid4().hex

    responses.add(
        method=responses.POST,
        url=f"{SigmaBaseUrl.AWS_US.value}/v2/auth/token",
        json={"access_token": fake_access_token},
        status=200,
    )

    return fake_access_token
