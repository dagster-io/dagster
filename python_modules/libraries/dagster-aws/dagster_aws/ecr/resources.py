import datetime

import boto3
from botocore.stub import Stubber
from dagster import resource


class ECRPublicResource:
    def __init__(self):
        self.client = boto3.client("ecr-public")

    def get_login_password(self):
        return self.client.get_authorization_token()["authorizationData"]["authorizationToken"]


class FakeECRPublicResource(ECRPublicResource):
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


@resource(
    description=(
        "This resource enables connecting to AWS Public and getting a login password from it."
        " Similar to the AWS CLI's `aws ecr-public get-login-password` command."
    )
)
def ecr_public_resource(_context):
    return ECRPublicResource()


@resource(
    description=(
        "This resource behaves like ecr_public_resource except it stubs out the real AWS API"
        " requests and always returns `'token'` as its login password."
    )
)
def fake_ecr_public_resource(_context):
    return FakeECRPublicResource()
