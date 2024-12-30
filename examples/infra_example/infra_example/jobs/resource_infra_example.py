from dagster import job, op

from infra_example.resources.terraform import terraform_stack, s3_bucket
import boto3

client = boto3.client("s3")


@op(required_resource_keys={"s3_bucket"})
def s3_op(context):
    context.log.info(context.resources.s3_bucket.config)
    response = client.get_bucket_location(Bucket=context.resources.s3_bucket.config["bucket"])
    return response["LocationConstraint"]


@job(resource_defs={"terraform_stack": terraform_stack, "s3_bucket": s3_bucket})
def resource_infra_example():
    s3_op()
