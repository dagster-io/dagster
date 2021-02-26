import os
import subprocess

from dagster import check

# We default to using the ECR region here
DEFAULT_AWS_ECR_REGION = "us-west-2"


def aws_ecr_repository(aws_account_id, aws_region=DEFAULT_AWS_ECR_REGION):
    """Returns the DNS hostname of the ECR registry for a given AWS account and region.

    Args:
        aws_account_id (str): Account ID, e.g. 123456789000
        aws_region (str, optional): AWS region to use. Defaults to DEFAULT_AWS_ECR_REGION.

    Returns:
        str: DNS hostname of the ECR registry to use.
    """
    check.str_param(aws_account_id, "aws_account_id")
    check.str_param(aws_region, "aws_region")

    return "{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com".format(
        aws_account_id=aws_account_id, aws_region=aws_region
    )


def get_aws_account_id():
    check.invariant(os.environ.get("AWS_ACCOUNT_ID"), "must have AWS_ACCOUNT_ID set")
    return os.environ.get("AWS_ACCOUNT_ID")


def get_aws_region():
    """Can override ECR region by setting the AWS_REGION environment variable."""
    return os.environ.get("AWS_REGION", DEFAULT_AWS_ECR_REGION)


def ensure_ecr_login(aws_region=DEFAULT_AWS_ECR_REGION):
    check.str_param(aws_region, "aws_region")

    cmd = "aws ecr get-login --no-include-email --region {} | sh".format(aws_region)

    check.invariant(
        subprocess.call(cmd, shell=True) == 0,
        "ECR login must succeed",
    )


def ecr_image(image, tag, aws_account_id, aws_region=DEFAULT_AWS_ECR_REGION):
    check.str_param(image, "image")
    check.str_param(aws_account_id, "aws_account_id")
    check.str_param(aws_region, "aws_region")

    return "{}/{}:{}".format(aws_ecr_repository(aws_account_id, aws_region), image, tag)
