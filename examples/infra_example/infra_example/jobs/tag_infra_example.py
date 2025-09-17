from dagster import job, op


from infra_example.resources.imports.aws.s3 import S3Bucket
from infra_example.resources.imports.aws import AwsProvider
from infra_example.resources.imports.aws.iam import IamRole

from cdktf import App, TerraformStack

import boto3

client = boto3.client("s3")


class S3Stack(TerraformStack):
    def __init__(self, _app: App, stack_name: str):
        self._app = _app
        super().__init__(_app, stack_name)
        AwsProvider(self, "Aws", region="us-west-2")
        S3Bucket(
            self,
            id="bucket",
            bucket="dagster-infra-tag-example",
        )


class RoleStack(TerraformStack):
    def __init__(self, _app: App, stack_name: str):
        super().__init__(_app, stack_name)
        AwsProvider(self, "Aws", region="us-west-2")
        IamRole(self, id="role", name="example-role", assume_role_policy="{}")


app = App()


@op(tags={"infrastructure/bucket": S3Stack(app, "s3_infra_example").to_terraform()})
def tagged_s3_op(context):
    context.log.info(context.resources.s3_bucket)
    response = client.get_bucket_location(Bucket=context.resources.s3_bucket.bucket)
    return response["LocationConstraint"]


@job(
    tags={
        "infrastructure/role": RoleStack(app, "iam_infra_example").to_terraform(),
    }
)
def tag_infra_example():
    tagged_s3_op()
