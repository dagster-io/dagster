import os

from dagster import check


def get_aws_account_id():
    check.invariant(os.environ.get('AWS_ACCOUNT_ID'), 'must have AWS_ACCOUNT_ID set')
    return os.environ('AWS_ACCOUNT_ID')


def aws_integration_image(aws_account_id, python_version, image_version):
    check.str_param(aws_account_id, 'aws_account_id')
    return "{aws_account_id}.dkr.ecr.us-west-1.amazonaws.com/{image}".format(
        aws_account_id=aws_account_id, image=integration_image(python_version, image_version),
    )


def integration_image(python_version, image_version):
    return 'buildkite-integration:py{python_version}-{image_version}'.format(
        python_version=python_version, image_version=image_version
    )


def local_integration_image(python_version, image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')
    return 'dagster/{image}'.format(image=integration_image(python_version, image_version))


def ensure_aws_login():
    check.invariant(
        os.system('aws ecr get-login --no-include-email --region us-west-1 | sh') == 0,
        'aws command must succeed',
    )


def local_test_builder_image():
    return 'dagster/test-image-builder:v2'


def aws_test_builder_image(aws_account_id):
    check.str_param(aws_account_id, 'aws_account_id')
    return "{aws_account_id}.dkr.ecr.us-west-1.amazonaws.com/test-image-builder:v2".format(
        aws_account_id=aws_account_id
    )
