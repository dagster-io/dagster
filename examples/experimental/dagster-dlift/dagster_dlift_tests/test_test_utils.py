import pytest
from dagster._core.test_utils import environ
from dagster_dlift.client import ENVIRONMENTS_SUBPATH
from dagster_dlift.gql_queries import VERIFICATION_QUERY
from dagster_dlift.test.client_fake import (
    DbtCloudClientFake,
    ExpectedAccessApiRequest,
    ExpectedDiscoveryApiRequest,
)
from dagster_dlift.test.utils import get_env_var


def test_get_env_var() -> None:
    """Test we can get an env var, and good error state for lack of env var."""
    with environ({"TEST_ENV_VAR": "test_value"}):
        assert get_env_var("TEST_ENV_VAR") == "test_value"

    with pytest.raises(Exception, match="TEST_ENV_VAR"):
        get_env_var("TEST_ENV_VAR")


def test_cloud_instance_fake() -> None:
    """Test that cloud instance fake behaves properly when inducing queries."""
    fake_instance = DbtCloudClientFake(
        access_api_responses={
            ExpectedAccessApiRequest(subpath=ENVIRONMENTS_SUBPATH): {
                "data": {"environments": [{"id": 1}]}
            }
        },
        discovery_api_responses={
            ExpectedDiscoveryApiRequest(query=VERIFICATION_QUERY, variables={"environmentId": 1}): {
                "data": {"environment": {"__typename": "Environment"}}
            }
        },
    )

    assert fake_instance.make_access_api_request(ENVIRONMENTS_SUBPATH) == {
        "data": {"environments": [{"id": 1}]}
    }
    assert fake_instance.make_discovery_api_query(VERIFICATION_QUERY, {"environmentId": 1}) == {
        "data": {"environment": {"__typename": "Environment"}}
    }
    with pytest.raises(Exception, match="ExpectedAccessApiRequest"):
        fake_instance.make_access_api_request("bad_subpath")
    with pytest.raises(Exception, match="ExpectedDiscoveryApiRequest"):
        fake_instance.make_discovery_api_query(VERIFICATION_QUERY, {"accountId": "bad"})
