import datetime
from typing import Optional

import boto3
from botocore.stub import Stubber
from dagster import ConfigurableResource, resource
from dagster._annotations import beta
from dagster._core.definitions.resource_definition import dagster_maintained_resource


class ECRPublicClient:
    def __init__(
        self,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        use_ssl: bool = True,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        verify: Optional[bool] = None,
    ):
        self.client = boto3.client(
            "ecr-public",
            region_name=region_name,
            use_ssl=use_ssl,
            verify=verify,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
        )

    def get_login_password(self):
        return self.client.get_authorization_token()["authorizationData"]["authorizationToken"]


class FakeECRPublicClient(ECRPublicClient):
    def get_login_password(self):
        with Stubber(self.client) as stubber:
            stubber.add_response(
                method="get_authorization_token",
                service_response={
                    "authorizationData": {
                        "authorizationToken": "token",
                        "expiresAt": datetime.datetime.now(),
                    }
                },
            )

            result = super().get_login_password()

            stubber.assert_no_pending_responses()

        return result


@beta
class ECRPublicResource(ConfigurableResource):
    """This resource enables connecting to AWS Public and getting a login password from it.
    Similar to the AWS CLI's `aws ecr-public get-login-password` command.
    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> ECRPublicClient:
        return ECRPublicClient()


@beta
class FakeECRPublicResource(ConfigurableResource):
    """This resource behaves like ecr_public_resource except it stubs out the real AWS API
    requests and always returns `'token'` as its login password.
    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> FakeECRPublicClient:
        return FakeECRPublicClient()


@beta
@dagster_maintained_resource
@resource(
    description=(
        "This resource enables connecting to AWS Public and getting a login password from it."
        " Similar to the AWS CLI's `aws ecr-public get-login-password` command."
    )
)
def ecr_public_resource(context) -> ECRPublicClient:
    return ECRPublicResource.from_resource_context(context).get_client()


@beta
@dagster_maintained_resource
@resource(
    description=(
        "This resource behaves like ecr_public_resource except it stubs out the real AWS API"
        " requests and always returns `'token'` as its login password."
    )
)
def fake_ecr_public_resource(context) -> FakeECRPublicClient:
    return FakeECRPublicResource.from_resource_context(context).get_client()
