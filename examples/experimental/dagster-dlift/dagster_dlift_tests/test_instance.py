import pytest
from dagster_dlift.cloud_instance import ENVIRONMENTS_SUBPATH
from dagster_dlift.gql_queries import VERIFICATION_QUERY
from dagster_dlift.test.instance_fake import (
    DbtCloudInstanceFake,
    ExpectedAccessApiRequest,
    ExpectedDiscoveryApiRequest,
)


def test_verification() -> None:
    """Test proper error states when we can't properly verify the instance."""
    # We get no response back from the discovery api
    fake_instance = DbtCloudInstanceFake(
        access_api_responses={
            ExpectedAccessApiRequest(subpath=ENVIRONMENTS_SUBPATH): {"data": [{"id": 1}]}
        },
        discovery_api_responses={
            ExpectedDiscoveryApiRequest(
                query=VERIFICATION_QUERY, variables={"environmentId": 1}
            ): {}
        },
    )

    with pytest.raises(Exception, match="Failed to verify"):
        fake_instance.verify_connections()

    # We get a response back from the discovery api, but it's not what we expect
    fake_instance = DbtCloudInstanceFake(
        access_api_responses={
            ExpectedAccessApiRequest(subpath=ENVIRONMENTS_SUBPATH): {"data": [{"id": 1}]}
        },
        discovery_api_responses={
            ExpectedDiscoveryApiRequest(query=VERIFICATION_QUERY, variables={"environmentId": 1}): {
                "data": {"environment": {"__typename": "NotEnvironment"}}
            }
        },
    )

    with pytest.raises(Exception, match="Failed to verify"):
        fake_instance.verify_connections()

    # Finally, we get a valid response back from the discovery api
    fake_instance = DbtCloudInstanceFake(
        access_api_responses={
            ExpectedAccessApiRequest(subpath=ENVIRONMENTS_SUBPATH): {"data": [{"id": 1}]}
        },
        discovery_api_responses={
            ExpectedDiscoveryApiRequest(query=VERIFICATION_QUERY, variables={"environmentId": 1}): {
                "data": {"environment": {"__typename": "Environment"}}
            }
        },
    )
    fake_instance.verify_connections()
