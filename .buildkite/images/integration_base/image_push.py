import os

import click
from automation.images import (
    aws_integration_base_image,
    execute_docker_push,
    get_aws_account_id,
    local_integration_base_image,
)

from dagster import check


@click.command()
@click.option('-v', '--python-version', type=click.STRING, required=True)
@click.option('-i', '--image_version', type=click.STRING, required=True)
def image_push(python_version, image_version):
    execute_image_push(python_version, image_version)


def execute_image_push(python_version, image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')
    check.invariant(os.environ.get('AWS_ACCOUNT_ID'), 'must have AWS_ACCOUNT_ID set')

    # always set cwd to the directory where the file lives
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    aws_image = aws_integration_base_image(
        aws_account_id=get_aws_account_id(),
        python_version=python_version,
        image_version=image_version,
    )
    local_image = local_integration_base_image(python_version, image_version)

    execute_docker_push(local_image=local_image, remote_image=aws_image)


if __name__ == '__main__':
    image_push()  # pylint: disable=no-value-for-parameter
