import os
import subprocess
from typing import Optional

import dagster._check as check

# We default to using the ECR region here
DEFAULT_AWS_ECR_REGION = "us-west-2"


def aws_ecr_repository(aws_account_id: str, aws_region: str = DEFAULT_AWS_ECR_REGION) -> str:
    """Returns the DNS hostname of the ECR registry for a given AWS account and region.

    Args:
        aws_account_id (str): Account ID, e.g. 123456789000
        aws_region (str): AWS region to use. Defaults to DEFAULT_AWS_ECR_REGION.

    Returns:
        str: DNS hostname of the ECR registry to use.
    """
    check.str_param(aws_account_id, "aws_account_id")
    check.str_param(aws_region, "aws_region")

    return f"{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com"


def get_aws_account_id() -> str:
    return check.not_none(os.environ.get("AWS_ACCOUNT_ID"), "must have AWS_ACCOUNT_ID set")


def get_aws_region() -> str:
    """Can override ECR region by setting the AWS_REGION environment variable."""
    return os.environ.get("AWS_REGION", DEFAULT_AWS_ECR_REGION)


def ensure_ecr_login(aws_region: str = DEFAULT_AWS_ECR_REGION):
    check.str_param(aws_region, "aws_region")

    cmd = "aws ecr get-login --no-include-email --region {} | sh".format(aws_region)

    check.invariant(
        subprocess.call(cmd, shell=True) == 0,
        "ECR login must succeed",
    )


def ecr_image(
    image: str, tag: Optional[str], aws_account_id: str, aws_region: str = DEFAULT_AWS_ECR_REGION
) -> str:
    check.str_param(image, "image")
    check.opt_str_param(aws_account_id, "tag")
    check.str_param(aws_account_id, "aws_account_id")
    check.str_param(aws_region, "aws_region")

    repo = aws_ecr_repository(aws_account_id, aws_region)
    tail = f"{image}:{tag}" if tag else image
    return f"{repo}/{tail}"
